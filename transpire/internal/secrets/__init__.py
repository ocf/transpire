from abc import ABC, abstractmethod

from transpire.manifestlike import ManifestLike


class SecretsProvider(ABC):
    @abstractmethod
    def convert_secret(self, secret: ManifestLike) -> dict:
        ...

    @abstractmethod
    def push_secret(self, secret: ManifestLike) -> None:
        ...
