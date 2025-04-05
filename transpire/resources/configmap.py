from pathlib import Path

from kubernetes import client

from transpire.resources.base import Resource


class ConfigMap(Resource[client.V1ConfigMap]):
    def __init__(
        self,
        name: str,
        *,
        data: dict[str, str],
    ):
        self.obj = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(
                name=name,
            ),
            data=data,
        )
        super().__init__()

    @staticmethod
    def from_files(name, files: list[Path]):
        data = {}
        for file in files:
            data[file.name] = file.read_text()
        return ConfigMap(name=name, data=data)
