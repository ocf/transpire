from pathlib import Path
from contextvars import ContextVar
from shutil import rmtree
from typing import Callable, Iterable, Union
from typing_extensions import Protocol
from .postprocessor import postprocess
import yaml


class ToDict(Protocol):
    def to_dict(self) -> dict:
        ...


ManifestLike = Union[dict, ToDict]

EmitBackendFunc = Callable[[Iterable[dict]], None]

_emit_backend: ContextVar[EmitBackendFunc] = ContextVar("_emit_backend")


def _coerce_dict(obj: ManifestLike) -> dict:
    if isinstance(obj, dict):
        return obj
    try:
        to_dict = getattr(obj, "to_dict")
        return to_dict()
    except AttributeError:
        pass
    raise TypeError("unsupported manifest type")


def emit(objs: Union[ManifestLike, Iterable[ManifestLike]]):
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

    backend(_coerce_dict(o) for o in objs_iter)


def write_manifests(objects: Iterable[dict], appname: str, manifest_dir: Path):
    """Write objects to manifest_dir as YAML files."""
    appdir = manifest_dir / appname
    if appdir.exists():
        rmtree(appdir)
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
