from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "transpire-github-webhook",
            "namespace": config.namespace,
            "annotations": {
                "cert-manager.io/cluster-issuer": "letsencrypt",
                "kubernetes.io/tls-acme": "true",
                "ingress.kubernetes.io/force-ssl-redirect": "true",
            },
        },
        "spec": {
            "ingressClassName": "contour",
            "rules": [
                {
                    "host": config.webhook_url.host,
                    "http": {
                        "paths": [
                            {
                                "path": config.webhook_url.path,
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "transpire-github-eventsource-svc",
                                        "port": {"number": 12000},
                                    }
                                },
                            }
                        ],
                    },
                }
            ],
            "tls": [
                {
                    "hosts": [config.webhook_url.host],
                    "secretName": "transpire-github-webhook-cert",
                }
            ],
        },
    }
