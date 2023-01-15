import tomllib
from typing import Dict, cast


def get_versions(caller) -> Dict[str, Dict[str, str]]:
    import pathlib

    file = pathlib.Path(caller).parent.resolve() / "versions.toml"

    return cast(
        Dict[str, Dict[str, str]],
        tomllib.loads(file.read_text()),
    )
