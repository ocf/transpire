from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "transpire-github",
            "namespace": config.namespace,
        },
        "spec": {
            "type": "ClusterIP",
            "selector": {
                "eventsource-name": "transpire-github",
            },
            "ports": [
                {
                    "port": 12000,
                    "protocol": "TCP",
                    "targetPort": 12000,
                },
            ],
        },
    }
