from transpire.internal.config import ClusterConfig
from transpire.internal.secrets.vault import VaultSecret
from transpire.types import ManifestLike


class ManifestError(Exception):
    def __init__(self, message: str, *, suggestion: ManifestLike | None) -> None:
        self.message = message
        self.suggestion = suggestion


def postprocess(
    config: ClusterConfig, obj: dict, appname: str, dev: bool = False
) -> dict:
    """Run all postprocessing steps (right now just secret processing)."""

    if obj["apiVersion"] == "v1" and obj["kind"] == "Secret":
        if config.secrets.provider == "vault":
            if not config.secrets.vault:
                raise ValueError("Options for Vault not provided.")
            provider = VaultSecret(config.secrets.vault, appname, dev)
            return provider.convert_secret(obj)

    return obj
