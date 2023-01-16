import base64
import os

import hvac  # type: ignore
import hvac.exceptions  # type: ignore
from pydantic import BaseModel

from transpire.internal.secrets import SecretsProvider
from transpire.types import ManifestLike, manifest_to_dict


class HashicorpVaultConfig(BaseModel):
    kvstore: str


def fix_base64(pairs: dict) -> dict:
    """Runs base64^-1(v) on every value in a dict."""
    return {k: base64.b64decode(v).decode() for k, v in pairs.items()}


def extract_secret(secret: dict) -> dict:
    """Takes a Kubernetes secret object, returns analogous Vault path and the k:v secrets."""
    # TODO: Handle generateName? Though who would put generateName on a secret? Does that even work???
    return {
        **fix_base64(safe_get(secret, "data")),
        **safe_get(secret, "stringData"),
    }


def safe_get(manifest: dict, key: str) -> dict:
    """
    A version of .get(key, {}).items() that correctly handles
    the case where manifest[key] is None, and not that it doesn't
    exist.
    """
    out = manifest.get(key, {})
    return out if out else {}


class VaultSecret(SecretsProvider):
    def __init__(
        self, config: HashicorpVaultConfig, ns: str, dev: bool = False
    ) -> None:
        self.kvstore = config.kvstore
        self.dev = dev
        self.ns = ns
        # TODO: Make this toggle-offable.
        self.push = dev

    def push_secret(self, secret: ManifestLike) -> None:
        """v1/Secret -> Hashicorp Vault"""
        secret = manifest_to_dict(secret)
        path = f"{self.ns}/{secret['metadata']['name']}"
        client = hvac.Client("https://vault.ocf.berkeley.edu")
        client.token = os.getenv("VAULT_TOKEN")
        if not client.token:
            print(
                "I couldn't find your VAULT_TOKEN env variable, so I can't push secrets to Vault.",
            )
        assert client.is_authenticated()
        client.secrets.kv.v2.configure(mount_point=self.kvstore)

        pairs = extract_secret(secret)
        try:
            client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=pairs,
                cas=0,
                mount_point=self.kvstore,
            )
        except hvac.exceptions.InvalidRequest as e:
            print(f"{e} -- Probably '{path}' already created, not re-creating")

    def convert_secret(self, secret: ManifestLike) -> dict:
        """v1/Secret -> ricoberger.de/v1alpha1/SealedSecret"""
        secret = manifest_to_dict(secret)
        path = f"{self.ns}/{secret['metadata']['name']}"

        if self.dev:
            return secret

        keys = [
            *[k for k, _ in safe_get(secret, "data").items()],
            *[k for k, _ in safe_get(secret, "stringData").items()],
        ]

        return {
            "apiVersion": "ricoberger.de/v1alpha1",
            "kind": "VaultSecret",
            "metadata": {"name": secret["metadata"]["name"]},
            "spec": {
                "keys": keys,
                "path": f"{self.kvstore}/{path}",
                "type": "Opaque",
            },
        }
