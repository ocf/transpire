from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "ClusterRole",
        "metadata": {
            "name": "transpire-ci",
        },
        "rules": [
            {
                "apiGroups": ["argoproj.io"],
                "resources": ["workflows"],
                "verbs": [
                    "get",
                    "list",
                    "watch",
                    "create",
                    "update",
                    "patch",
                    "delete",
                ],
            }
        ],
    }
