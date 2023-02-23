import sys
from pathlib import Path
from shutil import rmtree
from typing import Optional

import click
import yaml
from loguru import logger

from transpire.internal import render
from transpire.internal.config import ClusterConfig, get_config


@click.group()
def commands(**_) -> None:
    """tools related to Kubernetes objects"""
    pass


@commands.command()
@click.argument("out_path", envvar="TRANSPIRE_OBJECT_OUTPUT", type=click.Path())
def build(out_path, **_) -> None:
    """build objects, write them to a folder"""
    config = ClusterConfig.from_cwd()
    modules = [
        c.load_module_w_context(n, context=config) for n, c in config.modules.items()
    ]

    out_path = Path(out_path)
    out_path.mkdir(exist_ok=True, parents=True)

    for module in modules:
        logger.info(f"Building {module.name}")
        render.write_manifests(config, module.objects, module.name, out_path)

    # TODO: Disallow calling a transpire module "base", via Pydantic.
    logger.info("Writing bases")
    basedir = Path(out_path) / "base"
    if basedir.exists():
        rmtree(basedir)
    for module in modules:
        render.write_base(basedir, module)


@commands.command("print")
@click.argument("app_name", required=False)
def list_manifests(app_name: Optional[str] = None, **_) -> None:
    """build objects, print them to stdout"""
    module = get_config(app_name)
    yaml.safe_dump_all(module.objects, sys.stdout)


@commands.command()
@click.argument("app_name", required=True)
def apply(app_name: str, **_):
    """build objects, apply them to current kubernetes context"""
    return NotImplemented
