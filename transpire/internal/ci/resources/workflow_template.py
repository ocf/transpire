from argo_workflows.model_utils import model_to_dict  # type: ignore
from hera import Env, Parameter, Task, ValueFrom, WorkflowTemplate

from transpire.internal.config import CIConfig


def build(config: CIConfig):
    # Mirrors transpire.config.GitModuleConfig

    with WorkflowTemplate(
        "transpire-stub",
        service_account_name="transpire-ci",
        parameters=[
            Parameter("git", value_from=ValueFrom(event="payload.repository.url")),
            Parameter("branch", value_from=ValueFrom("payload.ref")),
            Parameter("dir", value="/"),
        ],
    ) as w:
        Task(
            "stub",
            image="ghcr.io/ocf/transpire",
            command=["python", "-m", "transpire.internal.stub"],
            env=[
                Env(name="GIT_URL", value=w.get_parameter("git").value),
                Env(name="GIT_BRANCH", value=w.get_parameter("branch").value),
                Env(name="DIR", value=w.get_parameter("dir").value),
            ],
        )

    obj = model_to_dict(w.build(), serialize=True)
    obj["metadata"]["namespace"] = config.namespace
    return obj
