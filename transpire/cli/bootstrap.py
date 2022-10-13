import textwrap
from pathlib import Path

import click
from loguru import logger


@click.group()
def commands(**kwargs):
    """tools related to bootstrapping (new cluster, new repository, etc)"""
    pass


@commands.command()
def kubernetes(**kwargs):
    """bootstrap kubernetes to pull from your cluster repository"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
@click.argument("path", type=click.Path(exists=True), default=".", required=False)
@click.option("-f", "--force", is_flag=True)
def repository(path, force, **kwargs) -> None:
    """initializes current working directory to be a transpire app repository"""
    path = Path(path)
    transpire_py = path / ".transpire.py"

    if (not force) and transpire_py.exists():
        logger.error(
            "Looks like this repository is already initialized. To reinitialize, rerun with --force."
        )
        return

    transpire_py.write_text(
        textwrap.dedent(
            """
            from transpire.dsl import emit
            from transpire.dsl.resources import Deployment

            # TODO: Replace me with the name for this app!
            name = "echoserver"

            # TODO: Replace me with the configuration for this app!
            def build():
                deployment = resources.Deployment.simple("echoserver", "k8s.gcr.io/echoserver", "8080")
                emit(deployment)
            """
        )
    )
    logger.info(
        f"Successfully initialized transpire app repository in {path.resolve().name}."
    )
