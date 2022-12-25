from typing import Dict, cast

import tomlkit


def get_versions(caller) -> Dict[str, Dict[str, str]]:
    import pathlib

    file = pathlib.Path(caller).parent.resolve() / "versions.toml"

    return cast(
        Dict[str, Dict[str, str]],
        tomlkit.parse(file.read_text()),
    )
