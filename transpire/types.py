from contextvars import Context
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Protocol

from kubernetes import client
from pydantic import BaseModel, Field

from transpire.internal import context


class ToDict(Protocol):
    """An object that can be converted to a dictionary. Useful for objects from github.com/kubernetes-client/python."""

    def to_dict(self) -> dict:
        ...


# Something that is possibly a Kubernetes manifest. No validation is performed.
ManifestLike = dict | ToDict


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


_api_client = client.ApiClient()


def manifest_to_dict(obj: ManifestLike) -> dict:
    if isinstance(obj, dict):
        return obj
    try:
        return _api_client.sanitize_for_serialization(obj)
    except AttributeError:
        pass
    raise TypeError(f"unsupported manifest type: {type(obj)}")


def manifests_to_dict(
    objs: ManifestLike | Iterable[ManifestLike | None],
) -> Iterable[dict]:
    objs_iter: Iterable[ManifestLike | None]
    if isinstance(objs, dict):
        objs_iter = [objs]
    else:
        if isinstance(objs, Iterable):
            objs_iter = objs
        else:
            objs_iter = [objs]

    return (manifest_to_dict(o) for o in objs_iter if o is not None)


class Module:
    """Transpire modules contain information about how to build and deploy applications to Kubernetes."""

    pymodule: ModuleType

    @property
    def name(self) -> str:
        return self.pymodule.name

    @cached_property
    def namespace(self) -> str:
        if hasattr(self.pymodule, "namespace"):
            return self.pymodule.namespace
        return self.pymodule.name

    def _enter_context(self):
        context.set_app_context(self)

    def _render_iter(self, function: str) -> Iterable[Any]:
        def _list() -> Iterable[Any]:
            self._enter_context()
            if hasattr(self.pymodule, function):
                return list(getattr(self.pymodule, function)())
            return []

        return Context().run(_list)

    @cached_property
    def images(self) -> List[Image]:
        return list(self._render_iter("images"))

    @cached_property
    def objects(self) -> List[dict]:
        return list(manifests_to_dict(self._render_iter("objects")))

    @cached_property
    def pipeline(self) -> List[dict]:
        return list(manifests_to_dict(self._render_iter("pipeline")))

    def __init__(self, pymodule: ModuleType):
        self.pymodule = pymodule
