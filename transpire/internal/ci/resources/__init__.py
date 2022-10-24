from transpire.internal.ci.resources import event_source, sensor, workflow_template
from transpire.internal.config import CIConfig


def build(config: CIConfig):
    return [
        workflow_template.build(config),
        event_source.build(config),
        sensor.build(config),
    ]
