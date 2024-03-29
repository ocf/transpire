from typing import Iterable, Protocol

from kubernetes import client


class OpenAPIObject(Protocol):
    """An object that can be converted to a dictionary. Useful for objects from github.com/kubernetes-client/python."""

    openapi_types: dict
    attribute_map: dict


# Something that is possibly a Kubernetes manifest. No validation is performed.
ManifestLike = dict | OpenAPIObject
_api_client = client.ApiClient()


def manifest_to_dict(obj: ManifestLike) -> dict:
    try:
        sanitized = _api_client.sanitize_for_serialization(obj)
        assert isinstance(sanitized, dict)
        return sanitized
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
