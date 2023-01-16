import click

from . import bootstrap, dev, obj, secrets

__all__ = ["bootstrap", "cli", "dev", "obj", "secrets"]


@click.group()
def cli() -> None:
    pass


cli.add_command(bootstrap.commands, "bootstrap")
cli.add_command(dev.commands, "dev")
cli.add_command(obj.commands, "object")
cli.add_command(secrets.commands, "secret")
