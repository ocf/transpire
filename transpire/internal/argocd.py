from transpire.internal.validation import is_valid_dnsname


def make_app(
    app_name: str,
    repo_url: str = "https://github.com/ocf/cluster.git",
    repo_branch: str = "HEAD",
) -> dict:
    if not is_valid_dnsname(app_name):
        raise ValueError(f"Expected a valid DNS name, but got {app_name} instead.")

    return {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Application",
        "metadata": {"name": app_name, "namespace": "argocd"},
        "spec": {
            "project": "default",
            "destination": {
                "server": "https://kubernetes.default.svc",
                "namespace": app_name,
            },
            "source": {
                "repoURL": repo_url,
                "path": f"{app_name}",
                "targetRevision": repo_branch,
            },
            "syncPolicy": {
                "syncOptions": [
                    "CreateNamespace=true",
                ],
            },
        },
    }
