import click

from transpire.internal import config


@click.group()
def commands(**_):
    """tools to aid development with transpire"""
    pass


@commands.command()
def schema(**_) -> None:
    """print the json schema for a transpire parent"""
    print(config.ClusterConfig.schema_json())
