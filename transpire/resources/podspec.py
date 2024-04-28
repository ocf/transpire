from typing import Self
from kubernetes import client


# This isn't a resource that can be instantiated directly, it's just a thin wrapper.
class PodSpec:
    obj: client.V1PodSpec

    def __init__(self, obj: client.V1PodSpec) -> None:
        self.obj = obj

    def _init_env(self, container_name: str | None = None) -> client.V1Container:
        container = self.get_container(container_name)

        if container.env_from is None:
            container.env_from = []
        if container.env is None:
            container.env = []

        return container

    def with_embedded_env(
        self, env: dict[str, str], *, container_name: str | None = None
    ) -> Self:
        container = self._init_env(container_name=container_name)
        container.env.extend(
            client.V1EnvVar(
                name=envvar_name,
                value=envvar_value,
            )
            for envvar_name, envvar_value in env.items()
        )
        return self

    def with_configmap_env(
        self,
        name: str,
        *,
        mapping: dict[str, str] | None = None,
        container_name: str | None = None,
    ) -> Self:
        container = self._init_env(container_name=container_name)
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

    def with_secret_env(
        self,
        name: str,
        *,
        mapping: dict[str, str] | None = None,
        container_name: str | None = None,
    ) -> Self:
        container = self._init_env(container_name=container_name)
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

    def with_configmap_volume(
        self, name: str, mount_path: str, *, container_name: str | None = None, keys: list[str] | None = None
    ) -> Self:
        container = self.get_container(container_name)
        if container.volume_mounts is None:
            container.volume_mounts = []

        if keys is None:
            container.volume_mounts.append(
                client.V1VolumeMount(
                    name=name,
                    mount_path=mount_path,
                )
            )
        else:
            for key in keys:
                container.volume_mounts.append(
                    client.V1VolumeMount(
                        name=name,
                        mount_path=f"{mount_path}/{key}",
                        sub_path=key,
                    )
                )

        container.volumes.append(
            client.V1Volume(
                name=name,
                config_map=client.V1ConfigMapVolumeSource(
                    name=name,
                ),
            )
        )

        return self

    def with_secret_volume(
        self, name: str, mount_path: str, *, container_name: str | None = None
    ) -> Self:
        container = self.get_container(container_name)
        if container.volume_mounts is None:
            container.volume_mounts = []

        container.volume_mounts.append(
            client.V1VolumeMount(
                name=name,
                mount_path=mount_path,
            )
        )

        container.volumes.append(
            client.V1Volume(
                name=name,
                secret=client.V1SecretVolumeSource(
                    secret_name=name,
                ),
            )
        )

        return self

    def with_pvc_volume(
        self, name: str, mount_path: str, *, container_name: str | None = None
    ) -> Self:
        container = self.get_container(container_name)
        if container.volume_mounts is None:
            container.volume_mounts = []

        container.volume_mounts.append(
            client.V1VolumeMount(
                name=name,
                mount_path=mount_path,
            )
        )

        container.volumes.append(
            client.V1Volume(
                name=name,
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=name,
                ),
            )
        )

        return self

    def with_arbitrary_volume(
        self,
        volume: client.V1Volume,
        mount_path: str,
        *,
        container_name: str | None = None,
    ) -> Self:
        container = self.get_container(container_name)
        if container.volume_mounts is None:
            container.volume_mounts = []

        container.volume_mounts.append(
            client.V1VolumeMount(
                name=volume.name,
                mount_path=mount_path,
            )
        )

        container.volumes.append(volume)
        return self

    def get_container(
        self, name: str | None = None, *, remove: bool = False
    ) -> client.V1Container:
        container_list = self.obj.containers

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

    def add_container(self, name: str, image: str) -> Self:
        container_list = self.obj.containers

        names = set(c.name for c in container_list)
        if name in names:
            raise ValueError(f"Can't use name {name}, already in use.")

        container_list.append(
            client.V1Container(
                name=name,
                image=image,
            )
        )
        return self

    def add_arbitrary_container(self, container: client.V1Container) -> int:
        container_list = self.obj.containers

        names = set(c.name for c in container_list)
        if container.name in names:
            raise ValueError(f"Can't use name {container.name}, already in use.")

        container_list.append(container)
        return len(container_list) - 1

    def with_probes(
        self,
        *,
        liveness: client.V1Probe | None = None,
        readiness: client.V1Probe | None = None,
        startup: client.V1Probe | None = None,
        container_name: str | None = None,
    ) -> Self:
        container = self.get_container(container_name)
        if liveness is not None:
            container.liveness_probe = liveness
        if readiness is not None:
            container.readiness_probe = readiness
        if startup is not None:
            container.startup_probe = startup
        return self
