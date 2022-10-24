from hera import Parameter, Workflow

from transpire.internal.config import CIConfig


def build(config: CIConfig):
    workflow = Workflow(
        "transpire-stub",
        workflow_template_ref="transpire-stub",
        parameters=[
            # TODO: Get these values from the argo event
            Parameter("git", "??"),
            Parameter("branch", "??"),
            Parameter("dir", "??"),
        ],
    )

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
                            "source": {"resource": workflow.build()},
                        },
                    },
                    "retryStrategy": {"steps": 3},
                }
            ],
        },
    }
