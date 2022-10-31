import importlib
import importlib.util
import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Literal, Optional

import tomlkit
from pydantic import AnyUrl, BaseModel, Field

from transpire.internal.secrets.bitnamisealedsecrets import BitnamiSealedSecretsConfig
from transpire.types import Module


def first_env(*args: str, default: str | None = None) -> str:
    """
    try all environment variables in order, returning the first one that's set

    >>> import os
    >>> os.environ["VAR_THAT_EXISTS"] = "this exists!"
    >>> first_env("THIS_DOESNT_EXIST", "THIS_DOESNT_EITHER", "VAR_THAT_EXISTS")
    "this exists!"
    >>> first_env("THIS_DOESNT_EXIST", default="foo")
    "foo"
    """

    if len(args) == 0:
        if default is None:
            raise KeyError(
                "Unable to pull from environment, and no default was provided."
            )
        return default
    return os.environ.get(args[0], first_env(*args[1:], default=default))


class CLIConfig(BaseModel):
    """Configuration information for the transpire CLI tool."""

    git_path: Path = Field(description="Path to the git executable", default="git")
    cache_dir: Path = Field(description="The directory where cached files are stored")
    config_dir: Path = Field(
        description="The directory where transpire should write its persistent config files"
    )

    @classmethod
    @cache
    def from_env(cls) -> "CLIConfig":
        """pull configuration from environment variables, falling back to defaults as neccesary"""
        # TRANSPIRE_CACHE_DIR > XDG_CACHE_HOME > ~/.cache/
        cache_dir = (
            Path(first_env("TRANSPIRE_CACHE_DIR", "XDG_CACHE_HOME", default="~/.cache"))
            / "transpire"
        )

        # TRANSPIRE_CONFIG_DIR > XDG_CONFIG_HOME > ~/.config/
        config_dir = (
            Path(
                first_env(
                    "TRANSPIRE_CONFIG_DIR", "XDG_CONFIG_HOME", default="~/.config"
                )
            )
            / "transpire"
        )
        return cls(cache_dir=cache_dir.expanduser(), config_dir=config_dir.expanduser())


def load_py_module_from_file(
    py_mod_name: str, path: Path, expected_app_name: str | None = None
) -> ModuleType:
    spec = importlib.util.spec_from_file_location(py_mod_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"No Python module was found at {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        real_app_name = module.name
    except AttributeError:
        raise ValueError(
            f"Python module at {path} does not appear to be a transpire module - missing `name'"
        )
    if expected_app_name is not None and real_app_name != expected_app_name:
        raise ValueError(
            f"Python module at {path} has wrong name: expected {expected_app_name}, got {real_app_name}"
        )

    return module


class ModuleConfig(ABC):
    @abstractmethod
    def load_py_module(self, name: str) -> ModuleType:
        ...

    def load_module(self, name: str) -> Module:
        return Module(self.load_py_module(name))


class LocalModuleConfig(ModuleConfig, BaseModel):
    path: Path = Field(
        description="The path to the transpire config file within the module"
    )

    def load_py_module(self, name: str) -> ModuleType:
        # TODO: do something about the implicit assumption that cwd == root of cluster repo
        # TODO: handle escaping file stem, make ".transpire.py" sane
        return load_py_module_from_file(
            re.sub("[^A-Za-z0-9_]", "_", self.path.stem),
            self.path,
            name,
        )

    @classmethod
    @cache
    def from_local(cls, path: Path | None = None) -> "LocalModuleConfig":
        raise NotImplementedError()


class GitModuleConfig(ModuleConfig, BaseModel):
    git: AnyUrl = Field(
        description="The URL of the remote git repository the module resides in"
    )
    branch: str | None = Field(description="The branch to deploy from")
    dir: Path = Field(
        description="The root path containing the module", default=Path(".")
    )

    def get_cached_repo(self) -> Path:
        config = CLIConfig.from_env()
        modules_cache_dir = config.cache_dir / "remote_modules"
        cache_dir = modules_cache_dir / re.sub("[^A-Za-z0-9]", "_", self.git)
        modules_cache_dir.mkdir(exist_ok=True, parents=True)

        if cache_dir.exists():
            branch = self.branch or "HEAD"
            try:
                subprocess.check_call(
                    [config.git_path, "remote", "set-url", "origin", self.git],
                    cwd=cache_dir,
                )
                subprocess.check_call(
                    [config.git_path, "fetch", "origin", branch, "--depth", "1"],
                    cwd=cache_dir,
                )
                subprocess.check_call(
                    [config.git_path, "reset", "--hard", f"origin/{branch}"],
                    cwd=cache_dir,
                )
                subprocess.check_call([config.git_path, "clean", "-dfx"], cwd=cache_dir)
            except subprocess.CalledProcessError:
                shutil.rmtree(cache_dir)
            else:
                return cache_dir

        cache_dir.mkdir(exist_ok=True, parents=True)
        branch_args = [] if self.branch is None else ["--branch", self.branch]
        subprocess.check_call(
            [
                config.git_path,
                "clone",
                "--depth",
                "1",
                "--single-branch",
                *branch_args,
                self.git,
                cache_dir,
            ],
            cwd=modules_cache_dir,
        )
        return cache_dir

    def load_py_module(self, name: str) -> ModuleType:
        cache_dir = self.get_cached_repo()
        return load_py_module_from_file(
            "_transpire", cache_dir / self.dir / ".transpire.py", name
        )


class CIConfig(BaseModel):
    """CI Configuration"""

    namespace: str = Field(description="kubernetes namespace", default="transpire")
    webhook_url: str = Field(description="github webhook url")


class ClusterConfig(BaseModel):
    """Cluster configuration"""

    class SecretsConfig(BaseModel):
        provider: Literal["bitnami"] = Field(description="secrets provider to use")
        bitnami: Optional[BitnamiSealedSecretsConfig] = Field(
            description="configuration for bitnami sealed secrets"
        )

    apiVersion: Literal["v1"]
    secrets: SecretsConfig = Field(description="configuration for the secrets provider")
    modules: dict[
        str,
        LocalModuleConfig | GitModuleConfig,
    ] = Field(description="list of modules to load")

    ci: CIConfig

    @classmethod
    @cache
    def from_cwd(cls, cwd: Path = Path.cwd()) -> "ClusterConfig":
        cluster_toml = cwd / "cluster.toml"
        if cluster_toml.exists():
            with open(cluster_toml, "r") as f:
                return cls.parse_obj(tomlkit.load(f))
        if cwd.is_mount() or (cwd / ".git").exists():
            raise FileNotFoundError(
                "cluster.toml not found up to current git or fs boundary"
            )
        return cls.from_cwd(cwd.parent)


def get_config(module_name: str | None = None, cwd: Path = Path.cwd()) -> Module:
    if module_name:
        cluster_config = ClusterConfig.from_cwd(cwd)
        module = cluster_config.modules.get(module_name)
        if module is not None and isinstance(
            module, (LocalModuleConfig, GitModuleConfig)
        ):
            return module.load_module(module_name)
        cluster_toml = cwd / "cluster.toml"
        raise ValueError(
            f"Python module at {cluster_toml} is missing module {module_name}"
        )

    transpire_py = cwd / ".transpire.py"
    if transpire_py.exists():
        return Module(load_py_module_from_file("_transpire", transpire_py, None))
    if cwd.is_mount() or (cwd / ".git").exists():
        raise FileNotFoundError(
            ".transpire.py not found up to current git or fs boundary"
        )
    return get_config(module_name, cwd.parent)
