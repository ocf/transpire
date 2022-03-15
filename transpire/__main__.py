import click
import os

from .cli import bootstrap
from .cli import dev
from .cli import image
from .cli import obj


@click.group()
def cli():
    pass


cli.add_command(bootstrap.commands, "bootstrap")
cli.add_command(dev.dev, "dev")
cli.add_command(image.commands, "image")
cli.add_command(obj.commands, "obj")

if __name__ == "__main__":
    os.environ["BETTER_EXCEPTIONS"] = "1"
    cli()
