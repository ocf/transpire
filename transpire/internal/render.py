from contextvars import ContextVar
from pathlib import Path
from shutil import rmtree
from typing import Callable, Iterable, Union

import yaml
from loguru import logger

from transpire.internal import argocd
from transpire.internal.config import ClusterConfig
from transpire.internal.postprocessor import ManifestError, postprocess
from transpire.internal.types import ManifestLike, coerce_dict

EmitBackendFunc = Callable[[Iterable[dict]], None]

_emit_backend: ContextVar[EmitBackendFunc] = ContextVar("_emit_backend")


def emit(objs: Union[ManifestLike, Iterable[ManifestLike]]) -> None:
    try:
        backend = _emit_backend.get()
    except LookupError:
        raise RuntimeError("cannot emit outside of a transpire build")

    objs_iter: Iterable[ManifestLike]
    if isinstance(objs, dict):
        objs_iter = [objs]
    else:
        if isinstance(objs, Iterable):
            objs_iter = objs
        else:
            objs_iter = [objs]

    backend(coerce_dict(o) for o in objs_iter)


def write_manifests(
    config: ClusterConfig, objects: Iterable[dict], appname: str, manifest_dir: Path
) -> None:
    """Write objects to manifest_dir as YAML files."""
    appdir = manifest_dir / appname
    if appdir.exists():
        rmtree(appdir)
    appdir.mkdir(exist_ok=True)

    failed = False
    processed_objs = {}

    for obj in objects:
        if obj is None:
            logger.warn(
                "Got a None object as a Kubernetes manifest, did something fail to build?"
            )
            continue
        try:
            obj = postprocess(config, obj, dev=False)
        except ManifestError as err:
            name = obj["metadata"].get("name", obj["metadata"].get("generateName"))
            logger.exception(f"Error processing object: {name}")
            if err.suggestion:
                logger.info("Suggested replacement:")
                logger.info(err.suggestion)
            failed = True
            continue

        name = obj["metadata"].get("name", obj["metadata"].get("generateName", None))
        kind = obj["kind"]
        namespace = obj["metadata"].get("namespace", appname)
        if (
            obj["kind"] == "SyncedSecret"
            and (appdir / f"{name}_{kind}_{namespace}.yaml").exists()
        ):
            continue
        processed_objs[f"{name}_{kind}_{namespace}.yaml"] = obj

    if failed:
        logger.error("Exceptions encountered, manifests will not be written.")

    for fname, obj in processed_objs.items():
        with open(appdir / fname, "w") as f:
            yaml.safe_dump(obj, f)


def write_bases(names: Iterable[str], manifest_dir: Path) -> None:
    """Generate ArgoCD Applications for each transpire module."""
    # TODO: refactor
    appdir = manifest_dir / "base"
    if appdir.exists():
        rmtree(appdir)
    appdir.mkdir(exist_ok=True)
    for name in names:
        obj = argocd.make_app(name)
        name = obj["metadata"].get("name", obj["metadata"].get("generateName", None))
        kind = obj["kind"]
        namespace = obj["metadata"].get("namespace", name)
        with open(appdir / f"{name}_{kind}_{namespace}.yaml", "w") as f:
            yaml.safe_dump(obj, f)
