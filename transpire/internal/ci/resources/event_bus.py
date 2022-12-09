from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "EventBus",
        "metadata": {
            "name": "default",
            "namespace": config.namespace,
        },
        "spec": {
            "nats": {
                "native": {},
            }
        },
    }
