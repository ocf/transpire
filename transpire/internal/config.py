import os
from functools import cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


def first_env(*args: str, default: Optional[str] = None) -> str:
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
            Path(
                first_env(
                    "TRANSPIRE_CACHE_DIR",
                    "XDG_CACHE_HOME",
                    default="~/.cache",
                )
            ).expanduser()
            / "transpire"
        )

        # TRANSPIRE_CONFIG_DIR > XDG_CONFIG_HOME > ~/.config/
        config_dir = (
            Path(
                first_env(
                    "TRANSPIRE_CONFIG_DIR",
                    "XDG_CONFIG_HOME",
                    default="~/.config",
                )
            ).expanduser()
            / "transpire"
        )
        return cls(cache_dir=cache_dir, config_dir=config_dir)
