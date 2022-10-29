from transpire.resources import Deployment

"""
This is the name of the current transpire module, which is used for:
1. The name of the ArgoCD `Application` CRD which owns these resources.
2. The default namespace that resources should be deployed to (i.e. if `namespace` isn't set on a resource, it won't be overridden).
3. Potentially other things(?)
"""
name = "echoserver"


def objects():
    deployment = Deployment.simple(
        name=name, image="k8s.gcr.io/echoserver", ports=["8080"]
    )
    # TODO: This causes transpire to error because `api_version` is emitted instead of `apiVersion` for some reason.
    # I need to work on stuff and don't know why, so removing for now.
    # emit(deployment)
