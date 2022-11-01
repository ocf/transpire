from transpire.internal.ci.resources import (
    event_bus,
    event_source,
    ingress,
    sensor,
    workflow_template,
)
from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return [
        workflow_template.build(config),
        event_bus.build(config),
        event_source.build(config),
        sensor.build(config),
        ingress.build(config),
    ]
