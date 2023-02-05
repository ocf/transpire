from typing import Callable, Generic, Self, TypeVar

from transpire.manifestlike import ManifestLike, manifest_to_dict

T = TypeVar("T", bound=ManifestLike)


class Resource(Generic[T]):
    obj: T
    patches: list

    def __init__(self):
        self.patches = []

    def patch(self, *fns: Callable[[dict], dict]) -> Self:
        self.patches.extend(fns)
        return self

    def build(self) -> dict:
        out = manifest_to_dict(self.obj)
        for patch in self.patches:
            out = patch(out)
        return out
