from __future__ import annotations

from typing import Optional, Union

from kubernetes import client


class Ingress:
    @staticmethod
    def simple(
        host: str,
        service_name: str,
        service_port: Union[int, str],
        ingress_name: Optional[str] = None,
        path_prefix: str = "/",
    ) -> client.V1Ingress:
        return client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=ingress_name if ingress_name else service_name,
                annotations={
                    "cert-manager.io/cluster-issuer": "letsencrypt",
                    "ingress.kubernetes.io/force-ssl-redirect": "true",
                    "io.cilium/websocket": "enabled",
                    "kubernetes.io/tls-acme": "true",
                },
            ),
            spec=client.V1IngressSpec(
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
