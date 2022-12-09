from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return {
        "apiVersion": "v1",
        "kind": "ClusterRoleBinding",
        "metadata": {
            "name": "transpire-ci",
        },
        "subjects": [
            {
                "namespace": "transpire",
                "kind": "ServiceAccount",
                "name": "transpire-ci",
            }
        ],
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": "transpire-ci",
        },
    }
