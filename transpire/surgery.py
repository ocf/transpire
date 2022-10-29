from collections.abc import Callable, Iterable

from transpire.internal.surgery import delve
from transpire.internal.surgery import edit_manifests as _edit_manifests
from transpire.internal.surgery import make_edit_manifest, shelve
from transpire.internal.types import ManifestLike, coerce_many_to_dicts


def edit_manifests(
    edits: dict[
        tuple[str, str] | tuple[tuple[str, str], str], Callable[[dict], dict | None]
    ],
    manifests: ManifestLike | Iterable[ManifestLike | None],
) -> list[dict]:
    return _edit_manifests(edits, coerce_many_to_dicts(manifests))


__all__ = ["delve", "shelve", "edit_manifests", "make_edit_manifest"]
