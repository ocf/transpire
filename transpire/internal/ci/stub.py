import os
from pathlib import Path

from argo_workflows.model_utils import model_to_dict  # type: ignore
from kubernetes import client, config

from transpire.internal.config import GitModuleConfig


def main() -> None:
    # TODO: Dependencies?????

    module_config = GitModuleConfig(
        git=os.environ["GIT_URL"],
        branch=os.environ["GIT_BRANCH"],
        dir=Path(os.environ["DIR"]),
    )

    module = module_config.load_module(None)
    workflow = model_to_dict(module.workflow().build(), serialize=True)

    config.load_incluster_config()
    api = client.CustomObjectsApi()
    api.create_namespaced_custom_object(
        "argoproj.io", "v1alpha1", "transpire", "workflows", workflow
    )


if __name__ == "__main__":
    main()
