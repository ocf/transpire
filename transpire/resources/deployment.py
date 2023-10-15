from typing import List, Self, Union

from kubernetes import client

from transpire.resources.base import Resource


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

    def _init_env(self, container_id: int) -> client.V1Container:
        container = self.obj.spec.template.spec.containers[container_id]

        if container.env_from is None:
            container.env_from = []
        if container.env is None:
            container.env = []

        return container

    def with_configmap_env(
        self, name: str, *, mapping: dict[str, str] | None = None, container_id: int = 0
    ) -> Self:
        container = self._init_env(container_id)
        if mapping is None:
            container.env_from.append(
                client.V1EnvFromSource(
                    config_map_ref=client.V1ConfigMapEnvSource(
                        name=name,
                    )
                )
            )
        else:
            container.env.extend(
                client.V1EnvVar(
                    name=envvar_name,
                    value_from=client.V1EnvVarSource(
                        config_map_key_ref=client.V1ConfigMapKeySelector(
                            name=name,
                            key=cm_key,
                        )
                    ),
                )
                for envvar_name, cm_key in mapping.items()
            )
        return self

    def with_secrets_env(
        self, name: str, *, mapping: dict[str, str] | None = None, container_id: int = 0
    ) -> Self:
        container = self._init_env(container_id)
        if mapping is None:
            container.env_from.append(
                client.V1EnvFromSource(
                    secret_ref=client.V1SecretEnvSource(
                        name=name,
                    )
                )
            )
        else:
            container.env.extend(
                client.V1EnvVar(
                    name=envvar_name,
                    value_from=client.V1EnvVarSource(
                        secret_key_ref=client.V1SecretKeySelector(
                            name=name,
                            key=secret_key,
                        )
                    ),
                )
                for envvar_name, secret_key in mapping.items()
            )
        return self

    def get_container(
        self, name: str | None = None, *, remove: bool = False
    ) -> client.V1Container:
        container_list = self.obj.spec.template.spec.containers

        if name is None:
            if len(container_list) != 1:
                raise ValueError("If multiple containers, must pass name.")
            return container_list[0]

        for i, container in enumerate(container_list):
            if container.name == name:
                if remove:
                    return container_list.pop(i)
                return container

        raise ValueError(f"No such container: {name}")

    def add_container(self, container: client.V1Container) -> int:
        container_list = self.obj.spec.template.spec.containers

        names = set(c.name for c in container_list)
        if container.name in names:
            raise ValueError(f"Can't use name {container.name}, already in use.")

        container_list.append(container)
        return len(container_list) - 1

    def get_selector(self) -> dict[str, str]:
        return {self.SELECTOR_LABEL: self.obj.metadata.name}
