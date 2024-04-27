from typing import Any, List, Self, Union

from kubernetes import client

from transpire.resources.base import Resource
from transpire.resources.podspec import PodSpec


class StatefulSet(Resource[client.V1StatefulSet]):
    SELECTOR_LABEL = "transpire.ocf.io/deployment"

    def __init__(
        self,
        name: str,
        image: str,
        ports: List[Union[str, int]],
        service_name: str,
        *,
        args: List[str] | None = None,
    ):
        self.obj = client.V1StatefulSet(
            api_version="apps/v1",
            kind="StatefulSet",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1StatefulSetSpec(
                replicas=1,
                service_name=service_name,
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

    def with_volume_template(
        self,
        name: str,
        size: str,
        access_modes: list[str],
        storage_class_name: str | None = None,
    ) -> Self:
        self.obj.spec.volume_claim_templates.append(
            client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1PersistentVolumeClaimSpec(
                    access_modes=access_modes,
                    resources=client.V1ResourceRequirements(requests={"storage": size}),
                    storage_class_name=storage_class_name,
                ),
            )
        )
        return self

    def with_arbitrary_volume_template(
        self, template: client.V1PersistentVolumeClaim
    ) -> Self:
        self.obj.spec.volume_claim_templates.append(template)
        return self

    def __getattr__(self, name: str) -> Any:
        return getattr(self.pod_spec(), name)
