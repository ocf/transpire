from pathlib import Path
import textwrap
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
def repository(path, force, **kwargs):
    """initializes current working directory to be a transpire app repository"""
    path = Path(path)
    transpire_py = path / ".transpire.py"
    transpire_toml = path / ".transpire.toml"

    if (not force) and (transpire_py.exists() or transpire_toml.exists()):
        logger.error(
            "Looks like this repository is already initialized. To reinitialize, rerun with --force."
        )
        return

    transpire_py.write_text(
        textwrap.dedent(
            """
            from transpire import emit
            from transpire import resources
            
            # TODO: Replace me with the configuration for this app!
            def build():
                deployment = resources.Deployment.simple("echoserver", "k8s.gcr.io/echoserver", "8080")
                emit(deployment)
            """
        )
    )
    transpire_toml.write_text(
        textwrap.dedent(
            f"""
            [[image]]
            name = "{path.resolve().name}"
            dockerfile = "Dockerfile"
            """
        )
    )
    logger.info(f"Successfully initialized transpire app repository in {path.resolve().name}.")
