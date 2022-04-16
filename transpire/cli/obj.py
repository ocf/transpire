from contextvars import Context
from importlib import resources
from typing import Iterable, List
from transpire.internal import render
import click
import importlib.util
import yaml
import sys


def get_module():
    spec = importlib.util.spec_from_file_location("remote_module", ".transpire.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_to_list() -> List[dict]:
    manifests: List[dict] = []

    def emit_backend(objs: Iterable[dict]):
        nonlocal manifests
        manifests.extend(objs)

    def go():
        render._emit_backend.set(emit_backend)
        get_module().build()

    ctx = Context()
    ctx.run(go)

    return manifests


@click.group()
def commands(**kwargs):
    """tools related to Kubernetes objects (.transpire.py)"""
    pass


@commands.command()
@click.argument("out_path", envvar="TRANSPIRE_OBJECT_OUTPUT", type=click.Path())
@click.argument("app_name", envvar="TRANSPIRE_APP_NAME", type=str)  # TODO: validate
def build(out_path, app_name, **kwargs):
    """build objects, write them to a folder"""
    manifests = build_to_list()

    render.write_manifests(manifests, app_name, out_path)


@commands.command()
def list(**kwargs):
    """build objects, pretty-list them to stdout"""
    manifests = build_to_list()
    yaml.safe_dump_all(manifests, sys.stdout)


@commands.command()
def apply(**kwargs):
    """build objects, apply them to current kubernetes context"""
    raise NotImplementedError("Not yet implemented!")
