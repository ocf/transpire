import importlib.util
import sys
from collections import defaultdict
from contextvars import Context
from types import ModuleType
from typing import Iterable, List, Optional

import click
import yaml

from transpire.internal import render
from transpire.internal.argocd import make_app
from transpire.internal.context import get_app_name


def get_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("remote_module", ".transpire.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_to_lists() -> dict[str, List[dict]]:
    manifests: dict[str, List[dict]] = defaultdict(list)

    def emit_backend(objs: Iterable[dict]):
        manifests[get_app_name()].extend(objs)

    def go():
        render._emit_backend.set(emit_backend)
        get_module().build()

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


@commands.command("list")
@click.argument("app_name", required=False)
def list_manifests(app_name: Optional[str] = None, **kwargs) -> None:
    """build objects, pretty-list them to stdout"""
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
