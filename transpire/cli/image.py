import click
from shutil import which as shutil_which
from tomlkit import parse as parse_toml
from subprocess import run, PIPE
from typing import List


@click.group()
def commands(**kwargs):
    """tools related to images (.transpire.toml)"""
    pass


@commands.command()
@click.option("--push/--no-push", default=False)
def build(push, **kwargs):
    """build defined images"""
    # must be passed kwarg `remote` if --push is set
    # tags not in .transpire.toml are passed through kwarg `additional_tags`

    # ensure we have buildkit installed
    if shutil_which("buildctl") is None:
        raise RuntimeError("You must install Buildkit to use this script.")

    # get remote and additional tags (like one by commit)
    remote: str = kwargs.get("remote", None)
    tags: List[str] = kwargs.get("additional_tags", [])

    if (push is None) and (remote is None):
        raise ValueError(f"Argument remote cannot be None when --push is set")

    # read the dockerfile path, app name, tags, context
    with open(f".transpire.toml", "r") as tomlFile:
        config = parse_toml(tomlFile.read())

    build_output: List[bytes] = []
    for build_data in config["build"]:

        dockerfile: str = f"./{build_data['dockerfile']}"
        name: str = build_data["name"]
        tags.extend(build_data["tags"])
        build_context: str = build_data.get("context", ".")

        # format the remote location to push to: "{remote}", "{remote}/{name}" or "{name}"
        repo: str = "/".join(filter(lambda arg: arg is not None, [remote, name]))
        if len(repo) < 1:
            raise Exception(f"Build target has no identifier: \n{build_data}")

        # build and push the image to each tag on that remote
        for tag in tags:
            build_dest: str = f"{repo}:{tag}"

            build_args = [
                "buildctl",
                "build",
                "--frontend",
                "dockerfile.v0",
                "--local",
                f"context={build_context}",
                "--local",
                f"dockerfile={dockerfile}",
                "--output",
                "type=image," + f"name={build_dest}," + f"push={'true' if push else 'false'}",
            ]

            build_output.append(run(build_args, check=True, stdout=PIPE).stdout)


@commands.command()
def push(**kwargs):
    """push defined images"""
    raise NotImplementedError("Not yet implemented!")


@commands.command()
def list(**kwargs):
    """list defined images"""
    raise NotImplementedError("Not yet implemented!")
