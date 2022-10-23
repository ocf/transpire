from abc import ABC

from transpire.internal.render import ManifestLike


class SecretsProvider(ABC):
    def convert_secret(self, secret: ManifestLike) -> ManifestLike:
        ...
