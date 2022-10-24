from hera import Env, Task, WorkflowTemplate

from transpire.internal.config import CIConfig


def build(config: CIConfig):
    # Mirrors transpire.config.GitModuleConfig

    with WorkflowTemplate("transpire-stub") as w:
        Task(
            "stub",
            image="ghcr.io/ocf/transpire",
            command=["python", "-m", "transpire.internal.stub"],
            env=[
                Env(name="GIT_URL", value=w.get_parameter("git")),
                Env(name="GIT_BRANCH", value=w.get_parameter("branch")),
                Env(name="DIR", value=w.get_parameter("dir")),
            ],
        )

    obj = w.build()
    obj["metadata"]["namespace"] = config.namespace
    return obj
