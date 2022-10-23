from io import BytesIO
from subprocess import PIPE, run

import yaml
from pydantic import BaseModel

from transpire.internal.render import ManifestLike, _coerce_dict
from transpire.internal.secrets import SecretsProvider


class BitnamiSealedSecrets(SecretsProvider):
    def __init__(self, cert: str) -> None:
        self._cert = cert
        super().__init__()

    def convert_secret(self, secret: ManifestLike) -> dict:
        """v1/Secret -> bitnami.com/?/SealedSecret"""

        process = run(
            ["kubeseal", "seal", "--cert", self._cert],
            stdin=BytesIO(yaml.dump(_coerce_dict(secret))),
            stdout=PIPE,
            check=True,
        )

        return yaml.safe_load(process.stdout)


class BitnamiSealedSecretsConfig(BaseModel):
    certificate: str
