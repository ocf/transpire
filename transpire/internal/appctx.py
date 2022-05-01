from contextvars import ContextVar, copy_context
from typing import Callable, ParamSpec, TypeVar

_current_app: ContextVar[str] = ContextVar("current_app")

T = TypeVar("T")
P = ParamSpec("P")


def set_app_name(name: str) -> None:
    _current_app.set(name)


def with_app_name(
    name: str, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs
) -> T:
    ctx = copy_context()

    def go() -> T:
        set_app_name(name)
        return func(*args, **kwargs)

    return ctx.run(go)


def get_app_name() -> str:
    return _current_app.get()


def get_current_namespace() -> str:
    return _current_app.get()
