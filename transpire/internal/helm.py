from __future__ import annotations

import os
import shutil
import tempfile
from subprocess import PIPE, run
from typing import Any, List, Tuple

import yaml

from transpire.internal.config import CLIConfig
from transpire.internal.context import get_current_namespace

__all__ = ["build_chart_from_versions", "build_chart"]


def assert_helm() -> None:
    """ensure helm binary is available"""

    if shutil.which("helm") is None:
        raise RuntimeError("`helm` must be installed and in your $PATH")


def exec_helm(args: List[str], check: bool = True) -> Tuple[bytes, bytes]:
    """executes a helm command and returns (stdout, stderr)"""

    config = CLIConfig.from_env()
    process = run(
        [
            "helm",
            "--registry-config",
            config.cache_dir / "helm" / "registry.json",
            "--repository-cache",
            config.cache_dir / "helm" / "repository",
            "--repository-config",
            config.cache_dir / "helm" / "repositories.yaml",
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
    exec_helm(["repo", "add", name, url], check=True)


def build_chart(
    repo_url: str,
    chart_name: str,
    name: str,
    version: str,
    values: dict = {},
    capabilities: List[str] = [],
) -> List[dict]:
    """build a helm chart and return a list of manifests"""

    add_repo(name, repo_url)

    values_file, values_file_name = tempfile.mkstemp(suffix=".yml")
    with open(values_file_name, "w") as f:
        f.write(yaml.dump(values))

    capabilities_flag = []
    if len(capabilities) > 0:
        capabilities_flag = ["--api-versions", ", ".join(capabilities)]

    # TODO: Capture `stderr` output and make available to tracing.
    stdout, _ = exec_helm(
        [
            "template",
            "-n",
            get_current_namespace(),
            "--values",
            values_file_name,
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

    os.close(values_file)
    os.unlink(values_file_name)
    return list(yaml.safe_load_all(stdout))


def build_chart_from_versions(
    name: str,
    versions: dict[str, Any],
    values: dict = {},
) -> list:
    """thin wrapper around build_chart that builds based off a versions dict"""

    return build_chart(
        repo_url=versions[name]["helm"],
        chart_name=versions[name].get("chart", name),
        name=name,
        version=versions[name]["version"],
        values=values,
    )
