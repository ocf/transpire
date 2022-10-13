import sys
from contextvars import Context
from typing import Iterable, List, Optional

import click
import yaml

from transpire.internal import render, context
from transpire.internal.argocd import make_app
from transpire.internal.context import get_app_name
from transpire.internal.config import ClusterConfig, ModuleConfig


def build_to_lists(module_name: str, module_config: ModuleConfig) -> list[dict]:
    manifests: list[dict] = list()

    def emit_backend(objs: Iterable[dict]):
        manifests[get_app_name()].extend(objs)

    def go():
        render._emit_backend.set(emit_backend)
        context._current_app.set(module_name)
        module_config.load_py_module().objects()

    ctx = Context()
    ctx.run(go)

    return manifests


@click.group()
def commands(**kwargs) -> None:
    """tools related to Kubernetes objects (.transpire.py)"""
    pass


@commands.command()
@click.argument("out_path", envvar="TRANSPIRE_OBJECT_OUTPUT", type=click.Path())
def build(out_path, **kwargs) -> None:
    """build objects, write them to a folder"""
    apps_manifests = build_to_lists()

    for app_name, manifests in apps_manifests.items():
        make_app(app_name)
        render.write_manifests(manifests, app_name, out_path)


@commands.command("print")
@click.argument("app_name", required=False)
def list_manifests(app_name: Optional[str] = None, **kwargs) -> None:
    """build objects, pretty-list them to stdout"""
    if app_name:
        config = ClusterConfig.from_cwd()
        module = config.modules.get(app_name)
        if not module:
            raise ModuleNotFoundError(f"Couldn't find {app_name} in cluster.toml.")
    else:
        raise NotImplementedError("Need to get the module from the cwd...")

    apps_manifests = build_to_lists()
    if app_name is None:
        keys: List[str] = list(apps_manifests.keys())
        if len(keys) == 1:
            app_name = keys[0]
        else:
            raise ValueError("Need app_name")
    yaml.safe_dump_all(apps_manifests[app_name], sys.stdout)


@commands.command()
def apply(**kwargs) -> None:
    """build objects, apply them to current kubernetes context"""
    raise NotImplementedError("Not yet implemented!")
