import os

import click

from transpire.internal.config import ClusterConfig, GitModuleConfig


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
        module_config = config.modules[module_name]

        if not isinstance(module_config, GitModuleConfig):
            click.echo("Building images is only supported for git modules", err=True)
            return

        module = module_config.load_module(module_name)

        git_url = str(module_config.git)
        if not git_url.endswith(".git"):
            git_url += ".git"
        git_url += "#"
        if module_config.branch is not None:
            git_url += module_config.branch

        images = [
            {"name": x.name, "context": f"{git_url}:{x.resolved_path}"}
            for x in module.images
        ]

        print(os.environ["GITHUB_OUTPUT"])
        print(f"image_matrix={images}")

        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            print(f"image_matrix={images}", file=f)
