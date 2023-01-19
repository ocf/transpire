from __future__ import annotations

from contextvars import Context
from functools import cached_property
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Protocol

from hera import Env, SecretVolume, Task, Volume, Workflow
from kubernetes import client
from pydantic import BaseModel, Field

from transpire.internal import config, context


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
    def resolved_path(self):
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
    config: "config.ModuleConfig" | None

    def __init__(
        self,
        pymodule: ModuleType,
        context=None,
        config: "config.ModuleConfig" | None = None,
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

    def _enter_context(self):
        context.set_app_context(self)
        if self.glob_context is not None:
            context.set_global_context(self.glob_context)

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

    def workflow(self) -> Workflow:
        if self.config is None or not isinstance(self.config, config.GitModuleConfig):
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

            self.pipeline >> clone >> build

        return w
