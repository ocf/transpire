from transpire.dsl import emit
from transpire.dsl.resources import Deployment

"""
This is the name of the current transpire module, which is used for:
1. The name of the ArgoCD `Application` CRD which owns these resources.
2. The default namespace that resources should be deployed to (i.e. if `namespace` isn't set on a resource, it won't be overridden).
3. Potentially other things(?)
"""
name = "echoserver"


def build():
    deployment = Deployment.simple(
        name=name, image="k8s.gcr.io/echoserver", ports=["8080"]
    )
    emit(deployment)
