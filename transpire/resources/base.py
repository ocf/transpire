from typing import Callable, Generic, TypeVar

from transpire.manifestlike import ToDict

T = TypeVar("T", bound=ToDict)


class Resource(Generic[T]):
    obj: T

    def patch(self, *fns: Callable[[T], T]):
        for f in fns:
            self.obj = f(self.obj)

    def build(self) -> T:
        return self.obj

    def to_dict(self) -> dict:
        return self.obj.to_dict()
