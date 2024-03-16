import shutil
import urllib.parse
from subprocess import PIPE, run
from typing import Any

import yaml

from transpire.internal.config import CLIConfig
from transpire.internal.context import get_app_context

__all__ = ["build_kustomization_from_versions", "build_kustomization"]


def assert_kubectl() -> None:
    """ensure kubectl binary is available"""

    if shutil.which("kubectl") is None:
        raise RuntimeError("`kubectl` must be installed and in your $PATH")


def exec_kustomize(args: list[str], check: bool = True) -> tuple[bytes, bytes]:
    """executes a kustomize command and returns (stdout, stderr)"""

    config = CLIConfig.from_env()
    process = run(
        [
            "kubectl",
            "kustomize",
            *args,
        ],
        check=False,
        stdout=PIPE,
        stderr=PIPE,
    )

    if check and process.returncode != 0:
        raise ValueError(process.stderr)

    return (process.stdout, process.stderr)


def build_kustomization(
    repo_url: str,
    path: str,
    version: str,
) -> list[dict]:
    """build a kustomization and return a list of manifests"""

    kustomize_url = urllib.parse.urljoin(repo_url, path)
    full_url = urllib.parse.urlparse(f"{kustomize_url}")._replace(query=f"ref={version}")

    # TODO: Capture `stderr` output and make available to tracing.
    stdout, _ = exec_kustomize(
        [full_url.geturl()],
        check=True,
    )

    # save our souls
    # <https://github.com/prometheus-community/helm-charts/pull/2238>
    # <https://github.com/prometheus-operator/prometheus-operator/pull/4897>
    # <https://github.com/yaml/pyyaml/issues/89>
    # <https://github.com/allenporter/k8s-gitops/commit/304c64c57926d2747328c0803c246be7dd827fdd>
    yaml.constructor.SafeConstructor.add_constructor(
        "tag:yaml.org,2002:value", yaml.constructor.SafeConstructor.construct_yaml_str  # type: ignore
    )

    return list(yaml.safe_load_all(stdout))


def build_kustomization_from_versions(
    name: str,
    versions: dict[str, Any],
) -> list[dict]:
    """thin wrapper around build_chart that builds based off a versions dict"""

    return build_kustomization(
        repo_url=versions[name]["repo_url"],
        path=versions[name]["path"],
        version=versions[name]["version"],
    )
