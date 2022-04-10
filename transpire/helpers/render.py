from pathlib import Path
from typing import Iterable, Union
from .postprocessor import postprocess
import yaml


def emit(object: Union[dict, Iterable[dict]]):
    if object is dict:
        write_manifests([object], "appname", "manifest_dir")


def write_manifests(objects: Iterable[dict], appname: str, manifest_dir: Path):
    """Write objects to manifest_dir as YAML files."""
    appdir = manifest_dir / appname
    if appdir.exists():
        for p in set(appdir.glob("*")) - set(appdir.glob("*_SyncedSecret_*")):
            p.unlink()
    appdir.mkdir(exist_ok=True)
    for obj in objects:
        if obj is None:
            # TODO: Log message with warning
            continue
        obj = postprocess(obj, dev=False)
        name = obj["metadata"].get("name", obj["metadata"].get("generateName", None))
        kind = obj["kind"]
        namespace = obj["metadata"].get("namespace", appname)
        if (
            obj["kind"] == "SyncedSecret"
            and (appdir / f"{name}_{kind}_{namespace}.yaml").exists()
        ):
            continue
        with open(appdir / f"{name}_{kind}_{namespace}.yaml", "w") as f:
            yaml.safe_dump(obj, f)
