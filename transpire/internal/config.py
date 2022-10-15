import importlib
import os
import re
import subprocess
from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path
from types import ModuleType

import tomlkit
from pydantic import AnyUrl, BaseModel, Field


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
    py_mod_name: str, path: Path, expected_app_name: str
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
    if real_app_name != expected_app_name:
        raise ValueError(
            f"Python module at {path} has wrong name: expected {expected_app_name}, got {real_app_name}"
        )

    return module


class ModuleConfig(ABC):
    @abstractmethod
    def load_py_module(self, name: str) -> ModuleType:
        ...


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


class RemoteModuleConfig(ModuleConfig, BaseModel):
    git_url: AnyUrl = Field(
        description="The URL of the remote git repository the module resides in"
    )
    branch: str | None = Field(description="The branch to deploy from")
    directory: Path | None = Field(description="The root path containing the module")

    def load_py_module(self, name: str) -> ModuleType:
        config = CLIConfig.from_env()
        modules_cache_dir = config.CLIConfig.from_env().cache_dir / "remote_modules"
        cache_dir = modules_cache_dir / re.sub("[^A-Za-z0-9]", "_", self.git_url)

        if not cache_dir.exists():
            subprocess.check_call(
                [config.git_path, "clone", self.git_url], cwd=modules_cache_dir
            )
        else:
            subprocess.check_call(
                [config.git_path, "remote", "set-url", "origin", self.git_url],
                cwd=cache_dir,
            )
            subprocess.check_call([config.git_path, "fetch", "origin"], cwd=cache_dir)
            subprocess.check_call(
                [config.git_path, "reset", "--hard", "@{upstream}"], cwd=cache_dir
            )

        return load_py_module_from_file("_transpire", cache_dir / ".transpire.py", name)


class ClusterConfig(BaseModel):
    """Cluster configuration"""

    modules: dict[str, LocalModuleConfig | RemoteModuleConfig] = Field(
        description="The list of modules to load"
    )

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
