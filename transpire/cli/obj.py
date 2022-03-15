import click


@click.group()
def commands(**kwargs):
    """tools related to Kubernetes objects (.transpire.py)"""
    pass


@commands.command()
def build(**kwargs):
    """build objects, write them to a folder"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def list(**kwargs):
    """build objects, pretty-list them to stdout"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def apply(**kwargs):
    """build objects, apply them to current kubernetes context"""
    raise NotImplementedError("Not yet implemented!")
