import click


@click.group()
def commands(**kwargs):
    """tools related to bootstrapping (new cluster, new repository, etc)"""
    pass


@commands.command()
def kubernetes(**kwargs):
    """bootstrap kubernetes to pull from your cluster repository"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def repository(**kwargs):
    """initializes current working directory to be a transpire app repository"""
    raise NotImplementedError("Not yet implemented!")
