from collections.abc import Callable, Iterable

from transpire.internal.surgery import delve
from transpire.internal.surgery import edit_manifests as _edit_manifests
from transpire.internal.surgery import make_edit_manifest, shelve
from transpire.types import ManifestLike, manifests_to_dict


def edit_manifests(
    edits: dict[
        tuple[str, str] | tuple[tuple[str, str], str], Callable[[dict], dict | None]
    ],
    manifests: ManifestLike | Iterable[ManifestLike | None],
) -> list[dict]:
    return _edit_manifests(edits, manifests_to_dict(manifests))


__all__ = ["delve", "shelve", "edit_manifests", "make_edit_manifest"]
