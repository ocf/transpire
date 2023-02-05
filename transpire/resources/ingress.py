from __future__ import annotations

from typing import Optional, Union

from kubernetes import client

from transpire.internal.context import get_global_context
from transpire.resources.base import Resource

from .service import Service


class Ingress(Resource[client.V1Ingress]):
    @classmethod
    def from_svc(cls, svc: Service, host: str, path_prefix: str = "/"):
        built = svc.build()
        # TODO: Make sure there's only one port.
        return cls(
            host=host,
            service_name=built["metadata"]["name"],
            service_port=built["spec"]["ports"][0]["port"],
            path_prefix=path_prefix,
        )

    def __init__(
        self,
        *,
        host: str,
        service_name: str,
        service_port: Union[int, str],
        ingress_name: Optional[str] = None,
        path_prefix: str = "/",
    ):
        ctx = get_global_context()
        self.obj = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=ingress_name if ingress_name else service_name,
                annotations={
                    "cert-manager.io/cluster-issuer": ctx.defaults.certManagerIssuer,
                    "ingress.kubernetes.io/force-ssl-redirect": "true",
                    "io.cilium/websocket": "enabled",
                    "kubernetes.io/tls-acme": "true",
                    "projectcontour.io/websocket-routes": path_prefix,
                },
            ),
            spec=client.V1IngressSpec(
                ingress_class_name=ctx.defaults.ingressClass,
                rules=[
                    client.V1IngressRule(
                        host=host,
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path=path_prefix,
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            port=client.V1ServiceBackendPort(
                                                number=service_port,
                                            ),
                                            name=service_name,
                                        )
                                    ),
                                )
                            ]
                        ),
                    )
                ],
                tls=[
                    client.V1IngressTLS(
                        hosts=[host],
                        secret_name=f"{service_name}-tls",
                    )
                ],
            ),
        )
        super().__init__()
