from typing import Protocol


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
    raise TypeError("unsupported manifest type")
