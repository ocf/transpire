from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from transpire.internal.config import GitModuleConfig
from transpire.types import Image, Module


@dataclass
class ContainerRegistry:
    """Configuration for a container registry"""

    name: str
    url: str
    org: str

    def get_image_metadata(
        self, config: GitModuleConfig, module: Module, image: Image
    ) -> dict:
        """Generate metadata for an image in this registry"""
        base_tag = f"{self.url}/{self.org}/{module.name}/{image.name}"
        return {
            "tags": [
                f"{base_tag}:latest",
                f"{base_tag}:{module.revision}",
            ],
            "labels": {
                "org.opencontainers.image.url": config.clean_git_url,
                "org.opencontainers.image.source": config.clean_git_url,
                "org.opencontainers.image.created": datetime.now(
                    timezone.utc
                ).isoformat(),
                "org.opencontainers.image.revision": module.revision,
            },
        }

    @staticmethod
    def get_supported_registries() -> list[str]:
        return list(supported_registries.keys())

    @staticmethod
    def get_registry(name: str) -> "ContainerRegistry":
        if name not in supported_registries:
            raise ValueError(f"Unsupported registry: {name}")
        return supported_registries[name]


HARBOR = ContainerRegistry(
    name="harbor",
    url="harbor.ocf.berkeley.edu",
    org="ocf",
)

GHCR = ContainerRegistry(
    name="ghcr",
    url="ghcr.io",
    org="ocf",
)

supported_registries = {
    "harbor": HARBOR,
    "ghcr": GHCR,
}
