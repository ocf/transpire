from transpire.internal.config import ClusterConfig
from transpire.internal.secrets.bitnamisealedsecrets import BitnamiSealedSecrets
from transpire.internal.types import ManifestLike


class ManifestError(Exception):
    def __init__(self, message: str, *, suggestion: ManifestLike | None) -> None:
        self.message = message
        self.suggestion = suggestion


def postprocess(config: ClusterConfig, obj: dict, dev: bool = False) -> dict:
    """Run all postprocessing steps (right now just secret processing)."""

    # TODO: this errors for some reason sometimes

    if obj["apiVersion"] == "v1" and obj["kind"] == "Secret" and not dev:
        if config.secrets.provider == "bitnami":
            provider = BitnamiSealedSecrets(config.secrets.bitnami.cert_path)
            raise ManifestError(
                "Secret objects are disallowed. Use SealedSecret objects instead.",
                suggestion=provider.convert_secret(obj),
            )

    return obj
