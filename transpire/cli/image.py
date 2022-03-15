import click
import importlib.util


def get_module():
    spec = importlib.util.spec_from_file_location("remote_module", ".transpire.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@click.group()
def commands(**kwargs):
    """tools related to images (.transpire.toml)"""
    pass


@commands.command()
def build(**kwargs):
    """build defined images"""
    module = get_module()
    module.build()
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def push(**kwargs):
    """push defined images"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def list(**kwargs):
    """list defined images"""
    raise NotImplementedError("Not yet implemented!")
