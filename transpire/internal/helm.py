from __future__ import annotations

import shutil
import tempfile
from subprocess import PIPE, run
from typing import Any

import yaml

from transpire.internal.config import CLIConfig
from transpire.internal.context import get_current_namespace

__all__ = ["build_chart_from_versions", "build_chart"]


def assert_helm() -> None:
    """ensure helm binary is available"""

    if shutil.which("helm") is None:
        raise RuntimeError("`helm` must be installed and in your $PATH")


def exec_helm(args: list[str], check: bool = True) -> tuple[bytes, bytes]:
    """executes a helm command and returns (stdout, stderr)"""

    config = CLIConfig.from_env()
    process = run(
        [
            "helm",
            "--registry-config",
            str(config.cache_dir / "helm" / "registry.json"),
            "--repository-cache",
            str(config.cache_dir / "helm" / "repository"),
            "--repository-config",
            str(config.cache_dir / "helm" / "repositories.yaml"),
            *args,
        ],
        check=check,
        stdout=PIPE,
        stderr=PIPE,
    )

    return (process.stdout, process.stderr)


def add_repo(name: str, url: str) -> None:
    """add a repository to transpire's Helm repository list"""

    assert_helm()
    _, stderr = exec_helm(["repo", "add", name, url], check=True)
    if stderr:
        print(stderr.decode("utf-8"))


def build_chart(
    repo_url: str,
    chart_name: str,
    name: str,
    version: str,
    values: dict | None = None,
    capabilities: list[str] | None = None,
) -> list[dict]:
    """build a helm chart and return a list of manifests"""

    # TODO: avoid needing to setting capabilities for "normal" things
    # - maybe have a config file at cluster level?

    add_repo(name, repo_url)

    with tempfile.NamedTemporaryFile(suffix=".yml") as values_file:
        values_file.write(yaml.dump(values).encode("utf-8"))

        capabilities_flag = []
        if capabilities is not None and len(capabilities) > 0:
            capabilities_flag = ["--api-versions", ", ".join(capabilities)]

        # TODO: Capture `stderr` output and make available to tracing.
        stdout, _ = exec_helm(
            [
                "template",
                "-n",
                get_current_namespace(),
                "--values",
                values_file.name,
                "--include-crds",
                "--version",
                version,
                "--name-template",
                name,
                *capabilities_flag,
                f"{chart_name}/{chart_name}",
            ],
            check=True,
        )

    return list(yaml.safe_load_all(stdout))


def build_chart_from_versions(
    name: str,
    versions: dict[str, Any],
    values: dict = {},
) -> list[dict]:
    """thin wrapper around build_chart that builds based off a versions dict"""

    return build_chart(
        repo_url=versions[name]["helm"],
        chart_name=versions[name].get("chart", name),
        name=name,
        version=versions[name]["version"],
        values=values,
    )
