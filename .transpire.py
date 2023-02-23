from pathlib import Path

from transpire.types import Image

name = "transpire"


def objects():
    return []


def images():
    yield Image(name="transpire", path=Path("/"))
