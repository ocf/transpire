import click
from kubernetes import client, config

from transpire.internal.config import get_config, provider_from_context


@click.group()
def commands(**_):
    """secret management commands"""
    pass


@commands.command()
@click.argument("app_name", required=True)
def push(app_name: str, **_) -> None:
    """build secrets from this repository -> push to vault"""
    module = get_config(app_name)
    provider = provider_from_context(module.namespace)

    for o in module.objects:
        if o["apiVersion"] == "v1" and o["kind"] == "Secret":
            provider.push_secret(o)


@commands.command()
@click.option("-n", "--namespace")
@click.argument("name", required=True)
def pull(namespace: str, name: str, **_) -> None:
    """get secret from kubernetes -> push to vault"""
    config.load_kube_config()
    v1 = client.CoreV1Api()

    secret = v1.read_namespaced_secret(name, namespace)
    assert secret

    provider = provider_from_context(secret.metadata.namespace)
    provider.push_secret(secret)
