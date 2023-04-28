import importlib
import importlib.util
import os
import re
import shutil
import tomllib
from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path
from subprocess import CalledProcessError, check_output
from types import ModuleType
from typing import Literal, Optional

from pydantic import AnyUrl, BaseModel, Field

from transpire.internal.secrets import SecretsProvider
from transpire.internal.secrets.vault import HashicorpVaultConfig, VaultSecret
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
    def load_module(self, name: str | None) -> Module:
        ...

    def load_module_w_context(self, name: str | None, context) -> Module:
        module = self.load_module(name)
        module.glob_context = context
        return module


class LocalModuleConfig(ModuleConfig, BaseModel):
    path: Path = Field(
        description="The path to the transpire config file within the module"
    )

    def load_module(self, name: str | None) -> Module:
        # TODO: do something about the implicit assumption that cwd == root of cluster repo
        # TODO: handle escaping file stem, make ".transpire.py" sane
        return Module(
            load_py_module_from_file(
                re.sub("[^A-Za-z0-9_]", "_", self.path.stem),
                self.path,
                name,
            )
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

    @property
    def resolved_dir(self) -> Path:
        if self.dir.is_absolute():
            return self.dir.relative_to("/")
        return self.dir

    @property
    def clean_git_url(self):
        return self.git.removesuffix(".git") + ".git"

    def get_cached_repo(self, *, commit: str | None = None) -> tuple[Path, str]:
        config = CLIConfig.from_env()
        cache_root = config.cache_dir / "remote_modules"
        cache_dir = cache_root / re.sub("[^A-Za-z0-9]", "_", self.git)
        cache_root.mkdir(exist_ok=True, parents=True)

        def call_cached_git(*args):
            return check_output([config.git_path, *args], cwd=cache_dir)

        if commit is None:
            fetch_args = [self.branch or "HEAD", "--depth", "1"]
            branch_args = [] if self.branch is None else ["--branch", self.branch]
            clone_args = ["--depth", "1", "--single-branch", *branch_args]
        else:
            # FIXME lol --unshallow is not idempotent
            fetch_args = ["--depth=10000000"]
            clone_args = []

        if cache_dir.exists():
            try:
                call_cached_git("fetch", self.git, *fetch_args)
                call_cached_git("checkout", "--detach")
                call_cached_git("reset", "--hard", commit or "FETCH_HEAD")
                call_cached_git("clean", "-dfx")
            except CalledProcessError:
                shutil.rmtree(cache_dir)
            else:
                return cache_dir, call_cached_git("rev-parse", "HEAD").decode().strip()

        cache_dir.mkdir(exist_ok=True, parents=True)
        check_output([config.git_path, "clone", *clone_args, self.git, cache_dir])

        call_cached_git("checkout", "--detach")
        if commit is None:
            commit = call_cached_git("rev-parse", "HEAD").decode().strip()
        else:
            call_cached_git("reset", "--hard", commit)

        return cache_dir, commit

    def load_module(self, name: str | None, *, commit: str | None = None) -> Module:
        cache_dir, commit = self.get_cached_repo(commit=commit)
        py_module = load_py_module_from_file(
            "_transpire", cache_dir / self.resolved_dir / ".transpire.py", name
        )
        module = Module(py_module)
        module.revision = commit
        return module


class ClusterDefaults(BaseModel):
    ingressClass: str | None
    certManagerIssuer: str | None


class ClusterConfig(BaseModel):
    """Cluster configuration"""

    class SecretsConfig(BaseModel):
        provider: Literal["vault"] = Field(description="secrets provider to use")
        vault: Optional[HashicorpVaultConfig] = Field(
            description="configuration for bitnami sealed secrets"
        )

    apiVersion: Literal["v1"]
    secrets: SecretsConfig = Field(description="configuration for the secrets provider")
    modules: dict[
        str,
        LocalModuleConfig | GitModuleConfig,
    ] = Field(description="list of modules to load")
    defaults: ClusterDefaults

    @classmethod
    @cache
    def from_cwd(cls, cwd: Path = Path.cwd()) -> "ClusterConfig":
        cluster_toml = cwd / "cluster.toml"
        if cluster_toml.exists():
            return cls.parse_obj(tomllib.loads(cluster_toml.read_text()))
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
            return module.load_module_w_context(module_name, context=cluster_config)
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


def provider_from_context(
    namespace: str, dev: bool = False, config: ClusterConfig | None = None
) -> SecretsProvider:
    if not config:
        config = ClusterConfig.from_cwd()
    if config.secrets.provider == "vault":
        if not config.secrets.vault:
            raise ValueError("Options for Vault not provided.")
        return VaultSecret(config.secrets.vault, namespace, dev)
    raise ValueError("No valid secrets provider found.")
