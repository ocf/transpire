from transpire.internal.ci.resources import (
    cluster_role,
    cluster_role_binding,
    event_bus,
    event_source,
    ingress,
    sensor,
    service_account,
    workflow_template,
)
from transpire.internal.config import CIConfig

name = "ci"


def build(config: CIConfig):
    return [
        cluster_role.build(config),
        cluster_role_binding.build(config),
        service_account.build(config),
        workflow_template.build(config),
        event_bus.build(config),
        event_source.build(config),
        sensor.build(config),
        ingress.build(config),
    ]
