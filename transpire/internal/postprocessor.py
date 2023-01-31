from transpire.internal.config import ClusterConfig, provider_from_context
from transpire.manifestlike import ManifestLike


class ManifestError(Exception):
    def __init__(self, message: str, *, suggestion: ManifestLike | None) -> None:
        self.message = message
        self.suggestion = suggestion


def postprocess(
    config: ClusterConfig, obj: dict, appname: str, dev: bool = False
) -> dict:
    """run all postprocessing steps (right now just secret processing)"""

    provider = provider_from_context(appname, dev=dev, config=config)
    if obj["apiVersion"] == "v1" and obj["kind"] == "Secret":
        return provider.convert_secret(obj)

    return obj
