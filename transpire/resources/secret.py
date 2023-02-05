from typing import Optional

from kubernetes import client

from transpire.internal.context import get_app_context, get_global_context
from transpire.resources.base import Resource


class Secret(Resource[client.V1Secret]):
    def __init__(
        self,
        name: str,
        string_data: Optional[dict[str, str]],
        type: str = "Opaque",
    ):
        glob_ctx = get_global_context()
        assert glob_ctx.secrets.vault
        app_ctx = get_app_context()
        namespace = app_ctx.namespace

        self.obj = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace,
            ),
            type=type,
            string_data=string_data,
        )
