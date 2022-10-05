# DSL Re-exports (Stable API)
from transpire.internal.context import (
    get_app_name,
    get_current_namespace,
    set_app_name,
    with_app_name,
)
from transpire.internal.render import emit

from . import helm, resources, surgery

__all__ = [
    "get_app_name",
    "get_current_namespace",
    "set_app_name",
    "with_app_name",
    "emit",
    "helm",
    "resources",
    "surgery",
]
