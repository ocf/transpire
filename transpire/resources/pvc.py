from typing import Union

from kubernetes import client

from transpire.resources.base import Resource


class PersistentVolumeClaim(Resource[client.V1PersistentVolumeClaim]):
    def __init__(
        self,
        name: str,
        storage: str,
        access_modes: list[str],
        storage_class_name: str | None = None,
    ):
        self.obj = client.V1PersistentVolumeClaim(
            api_version="v1",
            kind="PersistentVolumeClaim",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1PersistentVolumeClaimSpec(
                resources=client.V1ResourceRequirements(requests={"storage": storage}),
                access_modes=access_modes,
                storage_class_name=storage_class_name,
            ),
        )
        super().__init__()
