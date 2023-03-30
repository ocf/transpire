from collections.abc import Iterable
from contextvars import Context
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, List, TypeVar

from pydantic import BaseModel, Field

from transpire.internal import context
from transpire.manifestlike import manifests_to_dict

_T = TypeVar("_T")


class Version(BaseModel):
    """An adelie (github.com/nikhiljha/adelie) compatible version definition."""

    version: str
    github: str | None = Field(
        description="A GitHub repository URL, used for release version checking."
    )
    helm: str | None
    chart: str | None


class Image(BaseModel):
    """Describes how to build an OCI image."""

    name: str
    path: Path

    @property
    def resolved_path(self) -> Path:
        if self.path.is_absolute():
            return self.path.relative_to("/")
        return self.path


class Module:
    """Transpire modules contain information about how to build and deploy applications to Kubernetes."""

    pymodule: ModuleType
    revision: str | None

    def __init__(self, pymodule: ModuleType, context=None):
        self.pymodule = pymodule
        self.glob_context = context

    @property
    def name(self) -> str:
        name = self.pymodule.name
        assert name != "base"
        return name

    @cached_property
    def namespace(self) -> str:
        if hasattr(self.pymodule, "namespace"):
            return self.pymodule.namespace
        return self.pymodule.name

    def _enter_context(self) -> None:
        context.set_app_context(self)
        if self.glob_context is not None:
            context.set_global_context(self.glob_context)

    def _render_fn(
        self, function: str, finalizer: Callable[[Any], _T], default: _T
    ) -> _T:
        def _list() -> Any:
            self._enter_context()
            if hasattr(self.pymodule, function):
                return finalizer(getattr(self.pymodule, function)())
            return default

        return Context().run(_list)

    def _render_iter(self, function: str) -> list[Any]:
        def finalizer(gen: Any) -> list[Any]:
            if not isinstance(gen, Iterable):
                raise ValueError(f"function `{function}` must be iterable")
            return list(gen)

        return self._render_fn(function=function, finalizer=finalizer, default=[])

    @cached_property
    def images(self) -> List[Image]:
        return list(self._render_iter("images"))

    @cached_property
    def objects(self) -> List[dict]:
        return list(manifests_to_dict(self._render_iter("objects")))
