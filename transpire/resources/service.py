from typing import Union

from kubernetes import client

from transpire.resources.base import Resource


class Service(Resource[client.V1Service]):
    def __init__(
        self,
        name: str,
        selector: dict[str, str],
        port_on_pod: Union[int, str],
        port_on_svc: Union[int, str],
    ):
        self.svc = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1ServiceSpec(
                selector=selector,
                ports=[client.V1ServicePort(port=port_on_svc, target_port=port_on_pod)],
            ),
        )
