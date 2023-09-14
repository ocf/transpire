import click

from . import bootstrap, dev, image, obj, secrets, utils

@click.command(cls=utils.AliasedGroup)
def cli() -> None:
    pass


cli.add_command(bootstrap.commands, "bootstrap")
cli.add_command(dev.commands, "dev")
cli.add_command(obj.commands, "object")
cli.add_command(image.commands, "image")
cli.add_command(secrets.commands, "secret")
