from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "EventSource",
        "metadata": {
            "name": "transpire-github",
            "namespace": config.namespace,
        },
        "spec": {
            "service": {
                "ports": [
                    {
                        "name": "main",
                        "port": 12000,
                        "targetPort": 12000,
                    }
                ]
            },
            "github": {
                "main": {
                    "organizations": ["ocf"],
                    "webhook": {
                        "endpoint": "/github",
                        "port": "12000",
                        "method": "POST",
                        "url": str(config.webhook_url),
                    },
                    "events": ["*"],
                    "insecure": False,
                    "active": True,
                    "contentType": "json",
                }
            },
        },
    }
