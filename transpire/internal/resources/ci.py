from typing import List


# We don't use the argo pyhton library because it doesn't typecheck anyway.
# The way it checks types is by calling _check_types(), which my IDE doesn't understand
# and I figure if I'm going to have to google anything anyway I'll just write a plain dict.
class CIPipeline:
    @staticmethod
    def event_source(url: str) -> List[dict]:
        return [
            {
                "apiVersion": "argoproj.io/v1alpha1",
                "kind": "EventSource",
                "metadata": {"name": "github"},
                "spec": {
                    "service": {"ports": [{"port": 12000, "targetPort": 12000}]},
                    "webhook": {
                        "github": {
                            "port": "12000",
                            "endpoint": "/github",
                            "method": "POST",
                        }
                    },
                },
            }
        ]

    @staticmethod
    def sensor(name: str, repo: str) -> dict:
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Sensor",
            "metadata": {"name": name},
            "spec": {
                "template": {"serviceAccountName": "operate-workflow-sa"},
                "dependencies": [
                    {
                        "name": "github",
                        "eventSourceName": "github",
                        "eventName": "github",
                        "filters": {
                            "dataLogicalOperator": "and",
                            "data": [
                                {
                                    "path": "repository.full_name",
                                    "type": "string",
                                    "value": [repo],
                                },
                                {
                                    "path": "pusher.email",
                                    "type": "string",
                                    "comparator": "!=",
                                    "value": "1-800-NOT-A-REAL-EMAIL@woah@example.com",
                                },
                            ],
                        },
                    }
                ],
                "triggers": [
                    {
                        "template": {
                            "name": "transpire-remote-build",
                            "k8s": {
                                "operation": "create",
                                "source": {
                                    "resource": {
                                        "apiVersion": "argoproj.io/v1alpha1",
                                        "kind": "Workflow",
                                        "metadata": {
                                            "generateName": "transpire-build-"
                                        },
                                        "spec": {
                                            "entrypoint": "main",
                                            "arguments": {
                                                "parameters": [
                                                    {
                                                        "name": "source-repo",
                                                        "value": "https://github.com/ocf/templates",
                                                    },
                                                    {
                                                        "name": "source-branch",
                                                        "value": "main",
                                                    },
                                                    {"name": "path", "value": ""},
                                                    {
                                                        "name": "cluster-repo",
                                                        "value": "https://github.com/ocf/cluster",
                                                    },
                                                    {
                                                        "name": "cluster-branch",
                                                        "value": "main",
                                                    },
                                                ]
                                            },
                                            "workflowTemplateRef": {
                                                "name": "transpire-remote-build",
                                                "clusterScope": False,
                                            },
                                        },
                                    }
                                },
                                "parameters": [
                                    {
                                        "src": {
                                            "dependencyName": "github",
                                            "dataKey": "body.clone_url",
                                        },
                                        "dest": "spec.arguments.parameters.0.value",
                                    },
                                    {
                                        "src": {
                                            "dependencyName": "github",
                                            "dataKey": "body.after",
                                        },
                                        "dest": "spec.arguments.parameters.1.value",
                                    },
                                ],
                            },
                        }
                    }
                ],
            },
        }

    def template(self) -> dict:
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "WorkflowTemplate",
            "metadata": {"name": "transpire-remote-build"},
            "spec": {
                "arguments": {
                    "parameters": [
                        {
                            "name": "source-repo",
                            "value": "https://github.com/ocf/templates",
                        },
                        {"name": "source-branch", "value": "main"},
                        {"name": "path", "value": ""},
                        {
                            "name": "cluster-repo",
                            "value": "https://github.com/ocf/cluster",
                        },
                        {"name": "cluster-branch", "value": "main"},
                    ]
                },
                "entrypoint": "main",
                "volumeClaimTemplates": [
                    {
                        "metadata": {"name": "work"},
                        "spec": {
                            "accessModes": ["ReadWriteOnce"],
                            "resources": {"requests": {"storage": "128Mi"}},
                        },
                    }
                ],
                "volumeClaimGC": {
                    "strategy": "OnWorkflowCompletion",
                },
                "templates": [
                    {
                        "name": "main",
                        "dag": {
                            "tasks": [
                                {
                                    "name": "clone",
                                    "template": "clone",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "repo",
                                                "value": "{{workflow.parameters.source-repo}}",
                                            },
                                            {
                                                "name": "branch",
                                                "value": "{{workflow.parameters.source-branch}}",
                                            },
                                        ]
                                    },
                                },
                                {
                                    "name": "objects",
                                    "template": "objects",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "path",
                                                "value": "{{workflow.parameters.path}}",
                                            }
                                        ]
                                    },
                                    "depends": "clone",
                                },
                                {
                                    "name": "image",
                                    "template": "image",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "path",
                                                "value": "{{workflow.parameters.path}}",
                                            },
                                        ]
                                    },
                                    "depends": "clone",
                                },
                                {
                                    "name": "test",
                                    "template": "test",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "path",
                                                "value": "{{workflow.parameters.path}}",
                                            },
                                        ]
                                    },
                                    "depends": "image",
                                },
                                {
                                    "name": "deploy",
                                    "template": "deploy",
                                    "arguments": {
                                        "parameters": [
                                            {
                                                "name": "repo",
                                                "value": "{{workflow.parameters.cluster-repo}}",
                                            },
                                            {
                                                "name": "branch",
                                                "value": "{{workflow.parameters.cluster-branch}}",
                                            },
                                            {
                                                "name": "path",
                                                "value": "{{workflow.parameters.path}}",
                                            },
                                        ]
                                    },
                                    "depends": "test && image && objects",
                                },
                            ]
                        },
                    },
                    {
                        "name": "clone",
                        "inputs": {
                            "parameters": [{"name": "repo"}, {"name": "branch"}]
                        },
                        "container": {
                            "volumeMounts": [{"mountPath": "/work", "name": "work"}],
                            "image": "alpine/git:v2.32.0",
                            "workingDir": "/work",
                            "args": [
                                "clone",
                                "--depth",
                                "1",
                                "--branch",
                                "{{inputs.parameters.branch}}",
                                "--single-branch",
                                "{{inputs.parameters.repo}}",
                                "source",
                            ],
                        },
                    },
                    {
                        "name": "objects",
                        "inputs": {"parameters": [{"name": "path"}]},
                        "container": {
                            "image": "harbor.ocf.berkeley.edu/transpire/runner:latest",
                            "volumeMounts": [{"mountPath": "/work", "name": "work"}],
                            "workingDir": "/work/source/{{inputs.parameters.path}}",
                            "env": [
                                {"name": "TRANSPIRE_CONTEXT", "value": "ci"},
                                {
                                    "name": "TRANSPIRE_OBJECT_OUTPUT",
                                    "value": "/work/objects",
                                },
                            ],
                            "command": ["transpire"],
                            "args": ["object", "build"],
                        },
                    },
                    {
                        "name": "image",
                        "inputs": {"parameters": [{"name": "path"}]},
                        "container": {
                            "image": "harbor.ocf.berkeley.edu/transpire/runner:latest",
                            "volumeMounts": [{"mountPath": "/work", "name": "work"}],
                            "workingDir": "/work/source/{{inputs.parameters.path}}",
                            "env": [
                                {"name": "TRANSPIRE_CONTEXT", "value": "ci"},
                            ],
                            "command": ["transpire"],
                            "args": ["image", "build", "--push"],
                        },
                    },
                    {
                        "name": "test",
                        "inputs": {"parameters": [{"name": "path"}]},
                        "container": {
                            "image": "harbor.ocf.berkeley.edu/transpire/runner:latest",
                            "volumeMounts": [{"mountPath": "/work", "name": "work"}],
                            "workingDir": "/work/source/{{inputs.parameters.path}}",
                            "env": [
                                {"name": "TRANSPIRE_CONTEXT", "value": "ci"},
                            ],
                            "command": ["transpire"],
                            "args": ["image", "test"],
                        },
                    },
                    {
                        "name": "deploy",
                        "inputs": {
                            "parameters": [{"name": "repo"}, {"name": "branch"}]
                        },
                        "container": {
                            "image": "harbor.ocf.berkeley.edu/transpire/runner:latest",
                            "volumeMounts": [{"mountPath": "/work", "name": "work"}],
                            "workingDir": "/work",
                            "env": [
                                {"name": "TRANSPIRE_CONTEXT", "value": "ci"},
                                {
                                    "name": "TRANSPIRE_OBJECT_OUTPUT",
                                    "value": "/work/objects",
                                },
                            ],
                            "command": ["transpire"],
                            "args": ["object", "push"],
                        },
                    },
                ],
            },
        }
