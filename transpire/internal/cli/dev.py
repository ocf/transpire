import click

from transpire.internal import config


@click.group()
def commands(**kwargs):
    """devtools? idk"""
    pass


@commands.command()
def schema(**kwargs) -> None:
    """print the json schema for a transpire parent"""
    print(config.ClusterConfig.schema_json())
