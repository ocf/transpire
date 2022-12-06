from contextvars import ContextVar
from typing import ParamSpec, TypeVar

_current_app: ContextVar[str] = ContextVar("current_app")
_current_ns: ContextVar[str] = ContextVar("current_ns")

T = TypeVar("T")
P = ParamSpec("P")


def set_app_name(name: str) -> None:
    _current_app.set(name)


def set_app_ns(ns: str) -> None:
    _current_ns.set(ns)


def get_app_name() -> str:
    return _current_app.get()


def get_app_ns() -> str:
    return _current_ns.get()
