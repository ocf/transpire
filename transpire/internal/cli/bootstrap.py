import textwrap
from pathlib import Path

import click
from loguru import logger


@click.group()
def commands(**_):
    """tools related to bootstrapping (new cluster, new repository, etc)"""
    pass


@commands.command()
def kubernetes(**_):
    """bootstrap kubernetes to pull from your cluster repository"""
    return NotImplemented


@commands.command()
@click.argument("path", type=click.Path(exists=True), default=".", required=False)
@click.option("-f", "--force", is_flag=True)
def repository(path, force, **_) -> None:
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
            from transpire.resources import Deployment

            \"\"\"
            This is the name of the current transpire module, which is used for:
            1. The name of the ArgoCD `Application` CRD which owns these resources.
            2. The default namespace that resources should be deployed to (i.e. if `namespace` isn't set on a resource, it won't be overridden).
            \"\"\"
            name = "echoserver"


            def objects():
                yield Deployment.simple(name=name, image="k8s.gcr.io/echoserver", ports=["8080"])
            """
        )
    )
    logger.info(
        f"Successfully initialized transpire app repository in {path.resolve().name}."
    )
