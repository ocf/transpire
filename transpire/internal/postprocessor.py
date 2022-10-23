from transpire.internal.secrets.bitnamisealedsecrets import BitnamiSealedSecrets


def postprocess(obj: dict, dev: bool = False) -> dict:
    """Run all postprocessing steps (right now just secret processing)."""
    if obj["apiVersion"] == "v1" and obj["kind"] == "Secret" and not dev:
        provider = BitnamiSealedSecrets("TODO")
        return provider.convert_secret(obj)

    return obj
