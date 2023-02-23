import os

import click

from transpire.internal.config import ClusterConfig


@click.group()
def commands(**_) -> None:
    """tools related to images"""
    pass


@commands.command()
@click.argument("module_name", required=True)
@click.option("-o", "--output", required=True, type=click.Choice(["gha"]))
def build(module_name, output) -> None:
    """build images"""

    if output == "gha":
        config = ClusterConfig.from_cwd()
        module = config.modules[module_name].load_module(module_name)

        images = [{"name": x.name, "path": str(x.resolved_path)} for x in module.images]

        print(os.environ["GITHUB_OUTPUT"])
        print(f"image_matrix={images}")

        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            print(f"image_matrix={images}", file=f)
