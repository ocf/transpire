from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "ricoberger.de/v1alpha1",
        "kind": "VaultSecret",
        "metadata": {
            "name": "harbor-credentials",
            "namespace": config.namespace,
        },
        "spec": {
            "keys": ["config.json"],
            "path": "kvv2/transpire/harbor-credentials",
            "type": "Opaque",
        },
    }
