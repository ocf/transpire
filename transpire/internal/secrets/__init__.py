from abc import ABC

from transpire.types import ManifestLike


class SecretsProvider(ABC):
    def convert_secret(self, secret: ManifestLike) -> ManifestLike:
        ...
