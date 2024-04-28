from typing import Any, List, Union

from kubernetes import client

from transpire.resources.base import Resource
from transpire.resources.podspec import PodSpec


class Deployment(Resource[client.V1Deployment]):
    SELECTOR_LABEL = "transpire.ocf.io/deployment"

    def __init__(
        self,
        name: str,
        image: str,
        ports: List[Union[str, int]],
        *,
        args: List[str] | None = None,
    ):
        self.obj = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={self.SELECTOR_LABEL: name}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={self.SELECTOR_LABEL: name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="main",
                                image=image,
                                image_pull_policy="IfNotPresent",
                                args=args,
                                ports=[
                                    client.V1ContainerPort(container_port=x)
                                    for x in ports
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )
        super().__init__()

    def pod_spec(self) -> PodSpec:
        return PodSpec(self.obj.spec.template.spec)

    def get_selector(self) -> dict[str, str]:
        return {self.SELECTOR_LABEL: self.obj.metadata.name}
