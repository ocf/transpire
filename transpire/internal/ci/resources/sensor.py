from argo_workflows.model_utils import model_to_dict
from hera import Env, Parameter, Task, Workflow

from transpire.internal.config import CIConfig

transform = """
event_name = event.headers["X-Github-Event"]
url = event.body.repository.url
_, _, branch = string.find(event.body.ref, "refs/heads/(.+)")
return {event_name=event_name, url=url, branch=branch}
"""


def build(config: CIConfig):
    with Workflow(
        "transpire-ci",
        generate_name="transpire-ci-",
        service_account_name="transpire-ci",
        parameters=[
            Parameter("git", value="<<PLACEHOLDER>>"),
            Parameter("branch", value="<<PLACEHOLDER>>"),
            Parameter("dir", value="/"),
        ],
    ) as w:
        Task(
            "stub",
            image="ghcr.io/ocf/transpire",
            command=["python", "-m", "transpire.internal.ci.stub"],
            env=[
                Env(name="GIT_URL", value=w.get_parameter("git").value),
                Env(name="GIT_BRANCH", value=w.get_parameter("branch").value),
                Env(name="DIR", value=w.get_parameter("dir").value),
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
            "template": {"serviceAccountName": "transpire-ci"},
            "dependencies": [
                {
                    "name": "github-push",
                    "eventSourceName": "transpire-github",
                    "eventName": "main",
                    "transform": {"script": transform},
                    "filters": {
                        "data": [
                            {
                                "path": "event_name",
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
                            "source": {"resource": model_to_dict(w.build(), serialize=True)},
                            "parameters": [
                                {
                                    "src": {
                                        "dependencyName": "github-push",
                                        "dataKey": "url",
                                    },
                                    "dest": "spec.arguments.parameters.0.value",
                                },
                                {
                                    "src": {
                                        "dependencyName": "github-push",
                                        "dataKey": "branch",
                                    },
                                    "dest": "spec.arguments.parameters.1.value",
                                },
                            ],
                        },
                    },
                    "retryStrategy": {"steps": 3},
                }
            ],
        },
    }
