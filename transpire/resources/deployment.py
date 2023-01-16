from typing import List, Union

from kubernetes import client


class Deployment:
    @staticmethod
    def simple(
        name: str,
        image: str,
        ports: List[Union[str, int]],
        command: List[str] | None = None,
        configs_env: List[str] | None = None,
        secrets_env: List[str] | None = None,
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
                                command=command if command else None,
                                image_pull_policy="IfNotPresent",
                                ports=[
                                    client.V1ContainerPort(container_port=x)
                                    for x in ports
                                ],
                                env_from=[
                                    *(
                                        [
                                            client.V1EnvFromSource(
                                                config_map_ref=client.V1ConfigMapEnvSource(
                                                    name=var,
                                                ),
                                            )
                                            for var in configs_env
                                        ]
                                        if configs_env
                                        else []
                                    ),
                                    *(
                                        [
                                            client.V1EnvFromSource(
                                                secret_ref=client.V1SecretEnvSource(
                                                    name=var,
                                                ),
                                            )
                                            for var in secrets_env
                                        ]
                                        if secrets_env
                                        else []
                                    ),
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )
