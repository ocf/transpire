import click
from shutil import which as shutil_which
from tomlkit import parse as parse_toml
from subprocess import run, PIPE

@click.group()
def commands(**kwargs):
    """tools related to images (.transpire.toml)"""
    pass


@commands.command()
def build(**kwargs):
    """build defined images"""

    # ensure we have buildkit installed
    if shutil_which("buildctl") is None:
        raise RuntimeError("You must install Buildkit to use this script.")

    # get remote and additional tags (like one by commit)
    remote: str  = kwargs.get('registry', None)
    tags: list = kwargs.get('additional_tags', [])

    # read the dockerfile path, app name, tags, context
    with open(f".transpire.toml", 'r') as tomlFile:
        config = parse_toml(tomlFile.read())
        
        build_data = config['build'][0]

        dockerfile: str = f"./{build_data['dockerfile']}"
        name: str = build_data['name']
        tags.extend(build_data['tags'])
        build_context: str = build_data.get('context', '.')
    
    # format the remote location to push to
    repo: str = f"{remote}" + (f'/{name}' if name is not None else '')
    
    # build and push the image to each tag on that remote
    for tag in tags:
        build_dest: str = f"{repo}:{tag}"    
        
        buildArgs = [
            "builtctl", "build",
            "--frontend", "dockerfile.v0",
            "--local", f"context={build_context}", 
            "--local", f"dockerfile={dockerfile}",
            "--output", 
                "type=image," + \
                f"name={build_dest}," + \
                "push=true" # not sure about this
        ]

        buildOutput = run(buildArgs, check=True, stdout=PIPE).stdout


@commands.command()
def push(**kwargs):
    """push defined images"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def list(**kwargs):
    """list defined images"""
    raise NotImplementedError("Not yet implemented!")
