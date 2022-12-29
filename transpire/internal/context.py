from contextvars import ContextVar

# TODO: fixme
from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:
    from transpire.internal.config import ClusterConfig
    from transpire.types import Module


_app_context: ContextVar["Module"] = ContextVar("current_app")
_current_global: ContextVar["ClusterConfig"] = ContextVar("current_global")

T = TypeVar("T")
P = ParamSpec("P")


def set_app_context(info: "Module") -> None:
    _app_context.set(info)


def set_global_context(context: "ClusterConfig") -> None:
    _current_global.set(context)


def get_app_context() -> "Module":
    return _app_context.get()


def get_global_context() -> "ClusterConfig":
    return _current_global.get()
