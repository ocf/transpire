from typing import Iterable, Protocol


class ToDict(Protocol):
    def to_dict(self) -> dict:
        ...


ManifestLike = dict | ToDict


def coerce_dict(obj: ManifestLike) -> dict:
    if isinstance(obj, dict):
        return obj
    try:
        to_dict = getattr(obj, "to_dict")
        return to_dict()
    except AttributeError:
        pass
    raise TypeError(f"unsupported manifest type: {type(obj)}")


def coerce_many_to_dicts(
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

    return (coerce_dict(o) for o in objs_iter if o != None)
