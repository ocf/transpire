from pathlib import Path
from shutil import rmtree
from typing import Iterable

import yaml
from loguru import logger

from transpire.internal import argocd
from transpire.internal.config import ClusterConfig
from transpire.internal.postprocessor import ManifestError, postprocess
from transpire.types import Module


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
        try:
            obj = postprocess(config, obj, appname, dev=False)
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
    else:
        for fname, obj in processed_objs.items():
            with open(appdir / fname, "w") as f:
                yaml.safe_dump(obj, f)


def write_base(basedir: Path, module: Module):
    basedir.mkdir(exist_ok=True)
    obj = argocd.make_app(module.name, module.namespace, auto_sync=module.auto_sync)
    argo_namespace = obj["metadata"].get("namespace")
    if not argo_namespace:
        raise ValueError("Argo Application has unset namespace.")
    with open(basedir / f"{module.name}_Application_{argo_namespace}.yaml", "w") as f:
        yaml.safe_dump(obj, f)
