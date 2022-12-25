from typing import Optional

from kubernetes import client

from transpire.internal.context import get_app_context, get_global_context


class Secret:
    @staticmethod
    def simple(
        name: str,
        string_data: Optional[dict[str, str]],
        type: str = "Opaque",
    ) -> client.V1Secret:
        glob_ctx = get_global_context()
        assert glob_ctx.secrets.vault
        app_ctx = get_app_context()
        namespace = app_ctx.namespace

        return client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(
                name=name,
                namespace=namespace,
            ),
            type=type,
            string_data=string_data,
        )
