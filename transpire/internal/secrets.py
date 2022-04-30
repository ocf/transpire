import base64
import os
import subprocess


def fix_base64(pairs: dict) -> dict:
    """Runs base64^-1(v) on every value in a dict."""
    return {k: base64.b64decode(v).decode() for k, v in pairs.items()}


def extract_secret(secret: dict) -> dict:
    """Takes a Kubernetes secret object, returns k:v secrets as dict."""
    return {**fix_base64(secret.get("data", {})), **secret.get("stringData", {})}


def encrypt_value(key: str, value: str) -> str:
    """Encrypt a secret with the public key of the cluster."""
    return subprocess.run(
        ["arcanum-cli", "encrypt", str(value)],
        env={"ARCANUM_PUB_KEY": key, "PATH": os.getenv("PATH", "")},
        capture_output=True,
    ).stdout.decode()


def convert_secret(secret: dict) -> dict:
    """Takes a Kubernetes secret object, encrypts it, returns SyncedSecret object."""
    pub_key = os.environ.get("ARCANUM_PUB_KEY")
    if pub_key is None:
        raise TypeError("ARCANUM_PUB_KEY must be set (got None)")
    if len(pub_key) == 44:
        raise ValueError("ARCANUM_PUB_KEY must be a valid arcanum public key")

    return {
        "apiVersion": "arcanum.njha.dev/v1",
        "kind": "SyncedSecret",
        "metadata": secret["metadata"],
        # Explicitly puts the key names in the object, so you can tell if a secret changed from `git diff`.
        "spec": {
            "data": {
                key: encrypt_value(pub_key, value).strip()
                for (key, value) in extract_secret(secret).items()
            },
            "pub_key": pub_key,
        },
    }
