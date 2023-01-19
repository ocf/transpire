from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": "transpire-ci-builder",
            "namespace": config.namespace,
        },
    }
