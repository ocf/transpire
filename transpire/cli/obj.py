from importlib import resources
from transpire.helpers import render
import click
import importlib.util


def get_module():
    spec = importlib.util.spec_from_file_location("remote_module", ".transpire.py")
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@click.group()
def commands(**kwargs):
    """tools related to Kubernetes objects (.transpire.py)"""
    pass


@commands.command()
@click.argument("out_path", envvar="TRANSPIRE_OBJECT_OUTPUT", type=click.Path(exists=True))
def build(out_path, **kwargs):
    """build objects, write them to a folder"""
    get_module().build()


@commands.command()
def list(**kwargs):
    """build objects, pretty-list them to stdout"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def apply(**kwargs):
    """build objects, apply them to current kubernetes context"""
    raise NotImplementedError("Not yet implemented!")
