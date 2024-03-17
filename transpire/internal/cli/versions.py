import click
import tomlkit

from transpire.internal.cli.utils import AliasedGroup
from transpire.internal import helm
from loguru import logger

from transpire.internal.config import ClusterConfig

@click.command(cls=AliasedGroup)
def commands(**_):
    """version management commands"""
    pass

def get_latest_version(doc, app_name: str):
    if "helm" in doc[app_name]:
        helm.add_repo(app_name, doc[app_name]["helm"])
        helm.update_repo(app_name)
        chart_name = doc[app_name]["chart"] if "chart" in doc[app_name] else app_name
        search_results = helm.search_repo(chart_name)
        latest_version_list = list(
            x for x in search_results if x["name"] == f"{app_name}/{chart_name}"
        )

        if len(latest_version_list) != 1:
            raise ValueError(f"expected 1 result, got {len(latest_version_list)}")
        latest_version = latest_version_list[0]["version"]
        return latest_version
    return None

@commands.command()
@click.option("-f", "--file")
@click.argument("app_name", required=True)
def update(app_name: str, file: str, **_) -> None:
    """update to the newest version of a given app"""
    doc = tomlkit.parse(open(file).read())
    latest_version = get_latest_version(doc, app_name)

    if latest_version != None and latest_version != doc[app_name]["version"]:
        logger.info(f"updating {app_name} from {doc[app_name]['version']} to {latest_version}")
        doc[app_name]["version"] = latest_version
        with open(file, "w") as f:
            f.write(tomlkit.dumps(doc))

@commands.command()
@click.argument("file", required=True)
def all_updates(file: str, **_) -> None:
    """list all available updates"""
    doc = tomlkit.parse(open(file).read())

    config = ClusterConfig.from_cwd()
    for name, _ in config.modules.items():
        if name not in doc:
            continue
        latest_version = get_latest_version(doc, name)

        if latest_version != doc[name]["version"]:
            logger.info(f"{name} can be updated from {doc[name]['version']} to {latest_version}")
