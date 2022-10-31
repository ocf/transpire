from pathlib import Path
from subprocess import PIPE, run
from typing import Iterable

import yaml
from pydantic import BaseModel, Field

from transpire.internal.secrets import SecretsProvider
from transpire.internal.surgery import edit_manifests
from transpire.types import ManifestLike, manifest_to_dict, manifests_to_dict


class BitnamiSealedSecrets(SecretsProvider):
    def __init__(self, cert: str) -> None:
        self._cert = cert
        super().__init__()

    def convert_secret(self, secret: ManifestLike) -> dict:
        """v1/Secret -> bitnami.com/?/SealedSecret"""

        process = run(
            ["kubeseal", "seal", "--cert", self._cert],
            input=yaml.dump(manifest_to_dict(secret)).encode("utf-8"),
            stdout=PIPE,
            check=True,
        )

        return yaml.safe_load(process.stdout)


class BitnamiSealedSecretsConfig(BaseModel):
    cert_path: Path = Field(description="Path to the certificate")


def merge_secrets(
    sealed_secrets: ManifestLike | Iterable[ManifestLike],
    manifests: ManifestLike | Iterable[ManifestLike | None],
) -> Iterable[dict]:
    sealed_secrets_resolved = manifests_to_dict(sealed_secrets)
    manifests_resolved = manifests_to_dict(manifests)

    return [
        *sealed_secrets_resolved,
        *edit_manifests(
            {
                (("v1", "Secret"), s["metadata"]["name"]): lambda _: None
                for s in sealed_secrets_resolved
            },
            manifests_resolved,
        ),
    ]
