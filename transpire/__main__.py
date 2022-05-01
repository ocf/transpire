import click

from .cli import bootstrap, dev, image, obj


@click.group()
def cli() -> None:
    pass


cli.add_command(bootstrap.commands, "bootstrap")
cli.add_command(dev.dev, "dev")
cli.add_command(image.commands, "image")
cli.add_command(obj.commands, "obj")

if __name__ == "__main__":
    cli()
