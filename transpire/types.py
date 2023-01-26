from __future__ import annotations

from collections.abc import Generator
from contextvars import Context
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterable, List, Protocol, TypeVar

from hera import Env, SecretVolume, Task, Volume, Workflow
from kubernetes import client
from pydantic import BaseModel, Field

# `config` is imported as `config_`, to avoid shadowing issue with mypy
from transpire.internal import config as config_
from transpire.internal import context

_T = TypeVar("_T")


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

    @property
    def resolved_path(self) -> Path:
        if self.path.is_absolute():
            return self.path.relative_to("/")
        return self.path


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
    config: config_.ModuleConfig | None

    def __init__(
        self,
        pymodule: ModuleType,
        context=None,
        config: config_.ModuleConfig | None = None,
    ):
        self.pymodule = pymodule
        self.glob_context = context
        self.config = config

    @property
    def name(self) -> str:
        return self.pymodule.name

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
            if not isinstance(gen, Generator):
                raise ValueError(f"function `{function}` must be a generator")
            return list(gen)

        return self._render_fn(function=function, finalizer=finalizer, default=[])

    @cached_property
    def images(self) -> List[Image]:
        return list(self._render_iter("images"))

    @cached_property
    def objects(self) -> List[dict]:
        return list(manifests_to_dict(self._render_iter("objects")))

    def pipeline(self) -> List[Task] | Task:
        def finalizer(val: Any) -> List[Task] | Task:
            if isinstance(val, Task):
                return val
            if isinstance(val, list):
                if all(isinstance(x, Task) for x in val):
                    return val
            raise ValueError("function `pipeline` must return Task or list[Task]")

        # mypy bug causing something to be inferred as List[<nothing>]
        return self._render_fn("pipeline", finalizer=finalizer, default=[])  # type: ignore

    def workflow(self) -> Workflow:
        if self.config is None or not isinstance(self.config, config_.GitModuleConfig):
            # this is kinda janky but idk how to resolve it
            raise ValueError("Only git modules can run ci")

        with Workflow(
            f"{self.name}-ci",
            generate_name=True,
            service_account_name="transpire-ci-builder",
        ) as w:
            # TODO: Fix storage class default
            volume = Volume(
                size="25Gi", mount_path="/build", storage_class_name="rbd-nvme"
            )

            clone = Task(
                "clone",
                image="alpine/git:2.36.3",
                args=[*self.config.clone_args(), "."],
                volumes=[volume],
                working_dir="/build/build",
            )

            build = [
                Task(
                    "build",
                    image="moby/buildkit:v0.10.6-rootless",
                    command=["buildctl-daemonless.sh"],
                    env=[
                        Env(
                            name="BUILDKITD_FLAGS",
                            value="--oci-worker-no-process-sandbox",
                        ),
                        Env(name="DOCKER_CONFIG", value="/docker"),
                    ],
                    args=[
                        "build",
                        "--frontend",
                        "dockerfile.v0",
                        "--local",
                        f"context={image.resolved_path}",
                        "--local",
                        f"dockerfile={image.resolved_path}",
                        "--output",
                        # TODO: Get the git hash
                        f"type=image,name=harbor.ocf.berkeley.edu/ocf/{self.name}/{image.name}:latest,push=true",
                    ],
                    volumes=[
                        volume,
                        SecretVolume(
                            secret_name="harbor-credentials",
                            mount_path="/docker",
                            name="harbor-credentials",
                        ),
                    ],
                    working_dir="/build/build",
                )
                for image in self.images
            ]

            # IMPORTANT: this type error is being ignored because this very specific
            # case executes correctly. Since `clone` is a single task,
            # `self.pipeline() >> clone` will also evaluate to a single task - either
            # `self.pipeline()` is `list[Task]`, causing `Task.__rrshift__` to be
            # invoked, which returns Task, OR `self.pipeline()` is `Task`, which
            # invokes `Task.__rshift__`, which returns the RHS (`clone`), which is a
            # `Task`. If `clone` ever becomes a list, this breaks (since there is no
            # way for Hera to override `list >> list`).
            self.pipeline() >> clone >> build  # type: ignore

        return w
