from abc import ABC, abstractmethod

from transpire.types import ManifestLike


class SecretsProvider(ABC):
    @abstractmethod
    def convert_secret(self, secret: ManifestLike) -> ManifestLike:
        ...
