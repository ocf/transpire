import click


@click.group()
def commands(**kwargs):
    """tools related to images (.transpire.toml)"""
    pass


@commands.command()
def build(**kwargs):
    """build defined images"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def push(**kwargs):
    """push defined images"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def list(**kwargs):
    """list defined images"""
    raise NotImplementedError("Not yet implemented!")
