from transpire.internal.ci.resources import (
    cluster_role,
    cluster_role_binding,
    event_bus,
    event_source,
    ingress,
    secret,
    sensor,
    service,
    service_account,
    service_account_builder,
)
from transpire.internal.config import CIConfig

name = "ci"


def build(config: CIConfig):
    return [
        cluster_role.build(config),
        cluster_role_binding.build(config),
        service_account.build(config),
        service_account_builder.build(config),
        secret.build(config),
        event_bus.build(config),
        event_source.build(config),
        sensor.build(config),
        service.build(config),
        ingress.build(config),
    ]
