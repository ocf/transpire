import click
import tomlkit

from transpire.internal.cli.utils import AliasedGroup
from transpire.internal import helm
from loguru import logger


@click.command(cls=AliasedGroup)
def commands(**_):
    """version management commands"""
    pass


@commands.command()
@click.option("-f", "--file")
@click.argument("app_name", required=True)
def update(app_name: str, file: str, **_) -> None:
    """update to the newest version of a given app"""
    doc = tomlkit.parse(open(file).read())

    if "helm" in doc[app_name]:
        helm.add_repo(app_name, doc[app_name]["helm"])
        helm.update_repo(app_name)
        chart_name = doc[app_name]["chart"] or app_name
        search_results = helm.search_repo(chart_name)
        latest_version_list = list(
            x for x in search_results if x["name"] == f"{app_name}/{chart_name}"
        )

        if len(latest_version_list) != 1:
            raise ValueError(f"expected 1 result, got {len(latest_version_list)}")
        latest_version = latest_version_list[0]["version"]

        if latest_version != doc[app_name]["version"]:
            logger.info(f"updating {app_name} from {doc[app_name]['version']} to {latest_version}")
            doc[app_name]["version"] = latest_version
            with open(file, "w") as f:
                f.write(tomlkit.dumps(doc))

        doc[app_name]["version"]
