import os

import click

from transpire.internal.cli.utils import AliasedGroup
from transpire.internal.config import ClusterConfig, GitModuleConfig
from transpire.internal.registry import ContainerRegistry


@click.command(cls=AliasedGroup)
def commands(**_) -> None:
    """tools related to images"""
    pass


@commands.command()
@click.argument("module_name", required=True)
@click.option("-o", "--output", required=True, type=click.Choice(["gha"]))
@click.option("--commit")
@click.option(
    "--registry",
    type=click.Choice(ContainerRegistry.get_supported_registries()),
    default="harbor",
    help="Container registry to use",
)
def build(module_name: str, output: str, commit: str | None, registry: str) -> None:
    """build images"""

    if output == "gha":
        config = ClusterConfig.from_cwd()
        module_config = config.modules[module_name]

        if not isinstance(module_config, GitModuleConfig):
            click.echo("Building images is only supported for git modules", err=True)
            return

        module = module_config.load_module(module_name, commit=commit)

        git_url = f"{module_config.clean_git_url}#"
        if module_config.branch is not None:
            git_url += module_config.branch

        registry_config = ContainerRegistry.get_registry(registry)

        images = [
            {
                "name": x.name,
                "context": f"{git_url}:{x.resolved_path}",
                **({"target": x.target} if x.target is not None else {}),
                **registry_config.get_image_metadata(module_config, module, x),
            }
            for x in module.images
        ]

        print(os.environ["GITHUB_OUTPUT"])
        print(f"image_matrix={images}")

        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            print(f"image_matrix={images}", file=f)
