# transpire

An opinionated way to do Kubernetes Git-Ops.

- Generate all Kubernetes objects from Python, not YAML.
- Use separate repositories to store your Python configuration.
  - One [main repository](https://ocf.io/gh/kubernetes) with core cluster infrastructure (CoreDNS, Cilium, ArgoCD, etc...)
  - Many separate app repositories with Dockerfiles ([ocf/templates](https://ocf.io/gh/templates), [ocf/jukebox](https://ocf.io/gh/jukebox), etc...)
- One [cluster repository](https://ocf.io/gh/cluster) to store generated Kubernetes configuration (for rollbacks + inspection).

## How does it work?

- Create a "cluster repository" (can be a branch) for every Kubernetes cluster you want to run. This repository will contain every object you want to deploy, rendered as YAML. It will be automatically maintained by CI -- you will only push to it in exceptional circumstances.
- Create one or more "app repositories" (can be branches) for every app you want to deploy.
  - We recommend using one app repository for core infrastructure (DNS, CNI, ArgoCD, Ingress, Storage, etc.), and separate repositories for apps that you want to run on Kubernetes.
  - In the root of each repository, include a `.transpire.py` file that does `import transpire` and generates your desired Kubernetes objects as Python dicts. The transpire library has helper functions for some common objects. Otherwise, you may want to `import kubernetes` for more help. Pass objects to `transpire.emit()` to return them.
  - In the root of each repository, include a `.transpire.toml` file that contains information about what containers to build. Built artifacts will be available to `.transpire.py` via `transpire.artifacts`.
  - To develop, run `transpire dev`. This will generate a `.transpire/objects/` folder with generated configuration and dummy container names.
- Use `transpire bootstrap` to bootstrap a Kubernetes cluster you've deployed.
  - Uses local `kubectl` credentials to install dependencies (ArgoCD, Cilium, CoreDNS).
  - Points ArgoCD at your cluster repository + automatically runs the first sync.
