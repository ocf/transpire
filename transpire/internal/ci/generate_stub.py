from hera import Env, Parameter, Task, WorkflowTemplate

# Mirrors transpire.config.GitModuleConfig
parameters = [
    Parameter("git"),  # Git URL
    Parameter("branch"),  # Git branch
    Parameter("dir"),  # Directory root
]

with WorkflowTemplate("stub", parameters=parameters) as w:
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


w.create()
