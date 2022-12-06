from argo_workflows.model_utils import model_to_dict
from hera import Workflow

from transpire.internal.config import CIConfig


def build(config: CIConfig):
    w = Workflow("transpire-stub", workflow_template_ref="transpire-stub")

    return {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Sensor",
        "metadata": {
            "name": "transpire-ci",
            "namespace": config.namespace,
        },
        "spec": {
            "dependencies": [
                {
                    "name": "github-push",
                    "eventSourceName": "transpire-github",
                    "eventName": "ocf",
                    "filters": {
                        "data": [
                            {
                                "path": "header.X-Github-Event",
                                "type": "string",
                                "value": ["push"],
                            },
                        ]
                    },
                }
            ],
            "triggers": [
                {
                    "template": {
                        "name": "transpire-stub",
                        "argoWorkflow": {
                            "operation": "submit",
                            "source": {
                                "resource": model_to_dict(w.build(), serialize=True)
                            },
                        },
                    },
                    "retryStrategy": {"steps": 3},
                }
            ],
        },
    }
