from pydantic import BaseModel

from transpire.internal.secrets import SecretsProvider


class HashicorpVaultConfig(BaseModel):
    kvstore: str


class VaultSecret(SecretsProvider):
    def __init__(
        self, config: HashicorpVaultConfig, ns: str, dev: bool = False
    ) -> None:
        self.kvstore = config.kvstore
        self.dev = dev
        self.ns = ns

    def convert_secret(self, secret: dict) -> dict:
        """v1/Secret -> ricoberger.de/v1alpha1/SealedSecret"""

        # TODO: Interactive flow to push secrets to Hashicorp Vault, if this isn't bootstrap and Vault is accessible.
        if self.dev:
            ...
            return secret

        keys = [
            *[k for k, _ in secret.get("data", {}).items()],
            *[k for k, _ in secret.get("stringData", {}).items()],
        ]

        return {
            "apiVersion": "ricoberger.de/v1alpha1",
            "kind": "VaultSecret",
            "metadata": {"name": secret["metadata"]["name"]},
            "spec": {
                "keys": keys,
                "path": f"{self.kvstore}/{self.ns}/{secret['metadata']['name']}",
                "type": "Opaque",
            },
        }
