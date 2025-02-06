import pathlib
import tomllib
from typing import Dict, cast

from transpire.internal.context import get_app_context
from transpire.types import ContainerRegistry, Image, Module


def get_revision() -> str | None:
    """Retrieves the current Transpire module's revision."""
    return get_app_context().revision


def get_images() -> Dict[str, Image]:
    """Retrieves the current Transpire module's images."""
    return {im.name: im for im in get_app_context().images}


def get_image_tag(
    name: str, module: Module | None = None, collapse_image_name: bool = True
) -> str:
    """
    Retrieves the current Transpire module's images.

    :param name: The name of the image to retrieve.
    :param module: The module to retrieve the image from.
    :param collapse_image_name: Whether to combine the module and image name when they
        are equal. Changes ocf/abc-abc to ocf/abc) when the module only includes one image
        of the same name. This is the default behavior for GHCR.
    """
    if module is None:
        module = get_app_context()
    for im in module.images:
        if im.name != name:
            continue
        match im.registry:
            case ContainerRegistry.ghcr:
                if (
                    collapse_image_name
                    and module.name == im.name
                    and len(module.images) == 1
                ):
                    return f"ghcr.io/ocf/{module.name}:{module.revision}"
                return f"ghcr.io/ocf/{module.name}-{im.name}:{module.revision}"
            case ContainerRegistry.harbor:
                return f"harbor.ocf.berkeley.edu/ocf/{module.name}/{im.name}:{module.revision}"
    raise ValueError(f"no image with name {name}")


def get_file(caller, filename: str) -> pathlib.Path:
    """
    Given the __file__ parameter of the calling file and
    the filename of an adjacent file, return the path to
    that file.
    """
    return pathlib.Path(caller).parent.resolve() / filename


def get_versions(caller) -> Dict[str, Dict[str, str]]:
    """
    Given the __file__ parameter of the calling file, return
    the contents of versions.toml cast to a dict.
    """
    file = get_file(caller, "versions.toml")

    return cast(
        Dict[str, Dict[str, str]],
        tomllib.loads(file.read_text()),
    )
