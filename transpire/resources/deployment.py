from typing import List, Union

from kubernetes import client


class Deployment:
    @staticmethod
    def simple(
        name: str,
        image: str,
        ports: List[Union[str, int]],
    ):
        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(match_labels={"app": name}),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(labels={"app": name}),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="deployment",
                                image=image,
                                image_pull_policy="Never",
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
