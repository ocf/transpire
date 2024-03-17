import os
from datetime import datetime, timezone

import click

from transpire.internal.cli.utils import AliasedGroup
from transpire.internal.config import ClusterConfig, GitModuleConfig
from transpire.types import Image, Module

REGISTRY = "harbor.ocf.berkeley.edu"


def image_metadata(config: GitModuleConfig, module: Module, image: Image):
    base_tag = f"{REGISTRY}/ocf/{module.name}/{image.name}"
    return {
        "tags": [
            f"{base_tag}:latest",
            f"{base_tag}:{module.revision}",
        ],
        "labels": {
            "org.opencontainers.image.url": config.clean_git_url,
            "org.opencontainers.image.source": config.clean_git_url,
            "org.opencontainers.image.created": datetime.now(timezone.utc).isoformat(),
            "org.opencontainers.image.revision": module.revision,
        },
    }


@click.command(cls=AliasedGroup)
def commands(**_) -> None:
    """tools related to images"""
    pass


@commands.command()
@click.argument("module_name", required=True)
@click.option("-o", "--output", required=True, type=click.Choice(["gha"]))
@click.option("--commit")
def build(module_name: str, output: str, commit: str | None) -> None:
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

        images = [
            {
                "name": x.name,
                "context": f"{git_url}:{x.resolved_path}",
                **({"target": x.target} if x.target is not None else {}),
                **image_metadata(module_config, module, x),
            }
            for x in module.images
        ]

        print(os.environ["GITHUB_OUTPUT"])
        print(f"image_matrix={images}")

        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            print(f"image_matrix={images}", file=f)
