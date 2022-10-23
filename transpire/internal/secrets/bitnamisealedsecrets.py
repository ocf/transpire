from pathlib import Path
from subprocess import PIPE, run

import yaml
from pydantic import BaseModel, Field, PrivateAttr

from transpire.internal.secrets import SecretsProvider
from transpire.internal.types import ManifestLike, coerce_dict


class BitnamiSealedSecrets(SecretsProvider):
    def __init__(self, cert: str) -> None:
        self._cert = cert
        super().__init__()

    def convert_secret(self, secret: ManifestLike) -> dict:
        """v1/Secret -> bitnami.com/?/SealedSecret"""

        process = run(
            ["kubeseal", "seal", "--cert", self._cert],
            input=yaml.dump(coerce_dict(secret)).encode("utf-8"),
            stdout=PIPE,
            check=True,
        )

        return yaml.safe_load(process.stdout)


class BitnamiSealedSecretsConfig(BaseModel):
    cert_path: Path = Field(description="Path to the certificate")
