from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class Build(BaseModel):
    """A Build represents an OCI image that has been or should be built."""

    name: str = Field(description='The name of the image to build, e.x. "webserver".')
    tags: Optional[List[str]] = Field(
        description="Additional tags that should be applied to this image."
    )
    dockerfile: Path = Field(description="Full path to a Dockerfile to build.")
    output: Optional[str] = Field(
        description="The output image, tagged by hash, e.x. 'harbor.ocf.berkeley.edu/{reponame}/{name}@sha256:0ecb2ad60'"
    )


class Test(BaseModel):
    """A Test represents an OCI image that runs tests."""

    name: Optional[str] = Field(
        description="The name of the test to build (currently unused)"
    )
    depends_on: List[str] = Field(description="The images that this test depends on.")
    dockerfile: Path = Field(
        description="The name of the test to build (currently unused)"
    )


class Config(BaseModel):
    """Config represents a transpire configuration object, for CI."""

    build: List[Build] = Field(description="A list of Builds.")
    test: List[Test] = Field(description="A list of Tests.")


def parse(str) -> Config:
    ...
