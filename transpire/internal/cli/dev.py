import click

from transpire.internal import config
from transpire.internal.cli.utils import AliasedGroup


@click.command(cls=AliasedGroup)
def commands(**_):
    """tools to aid development with transpire"""
    pass


@commands.command()
def schema(**_) -> None:
    """print the json schema for a transpire parent"""
    print(config.ClusterConfig.schema_json())
