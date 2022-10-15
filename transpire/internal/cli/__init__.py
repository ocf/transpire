import click

from . import bootstrap, dev, image, obj

__all__ = ["bootstrap", "cli", "dev", "image", "obj"]


@click.group()
def cli() -> None:
    pass


cli.add_command(bootstrap.commands, "bootstrap")
cli.add_command(dev.dev, "dev")
cli.add_command(image.commands, "image")
cli.add_command(obj.commands, "object")
