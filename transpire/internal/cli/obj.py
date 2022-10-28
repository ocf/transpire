import sys
from contextvars import Context
from pathlib import Path
from types import ModuleType
from typing import Iterable, Optional

import click
import yaml

from transpire.internal import context, render
from transpire.internal.config import ClusterConfig, GitModuleConfig


def build_to_lists(module: ModuleType) -> tuple[str, list[dict]]:
    """
    Given a transpire module, build its Kubernetes objects.

    Returns (namespace, objects)
    """
    manifests: list[dict] = list()
    namespace: str | None = None

    def emit_backend(objs: Iterable[dict]):
        manifests.extend(objs)

    def go():
        nonlocal namespace
        render._emit_backend.set(emit_backend)
        context.set_app_name(module.name)
        if hasattr(module, "ns"):
            context.set_ns(module.ns)
        namespace = context.get_current_namespace()
        module.objects()

    ctx = Context()
    ctx.run(go)

    assert namespace is not None

    return namespace, manifests


@click.group()
def commands(**kwargs) -> None:
    """tools related to Kubernetes objects (.transpire.py)"""
    pass


@commands.command()
@click.argument("out_path", envvar="TRANSPIRE_OBJECT_OUTPUT", type=click.Path())
def build(out_path, **kwargs) -> None:
    """build objects, write them to a folder"""

    apps_manifests: dict[str, tuple[str, list[dict]]] = {}

    config = ClusterConfig.from_cwd()

    for app, module in config.modules.items():
        py_module = module.load_py_module(app)
        apps_manifests[app] = build_to_lists(py_module)

    out_path = Path(out_path)
    out_path.mkdir(exist_ok=True, parents=True)

    names_and_namespaces: dict[str, str] = {}
    for app_name, (ns, manifests) in apps_manifests.items():
        names_and_namespaces[app_name] = ns
        render.write_manifests(config, manifests, app_name, out_path)

    # TODO: Disallow calling a transpire module "base", somehow?
    # Can pydantic do this?
    render.write_bases(names_and_namespaces, out_path)


@commands.command("print")
@click.argument("app_name", required=False)
def list_manifests(app_name: Optional[str] = None, **kwargs) -> None:
    """build objects, print them to stdout"""
    py_module = None
    if app_name:
        config = ClusterConfig.from_cwd()
        module = config.modules.get(app_name)

        # Failure: The module isn't in the config file.
        if not module:
            raise ModuleNotFoundError(f"Couldn't find {app_name} in cluster.toml.")
        # Failure: The module is a remote module.
        if isinstance(module, GitModuleConfig):
            raise ValueError(
                f"{app_name} is a remote module, you should run transpire in the remote repository instead."
            )

        py_module = module.load_py_module(app_name)
    else:
        raise NotImplementedError(
            "Need to iterate upwards to git root / fs boundary and get .transpire.py / load that."
        )

    apps_manifests = build_to_lists(py_module)
    yaml.safe_dump_all(apps_manifests, sys.stdout)


@commands.command()
def apply(**kwargs) -> None:
    """build objects, apply them to current kubernetes context"""
    raise NotImplementedError("Not yet implemented!")
