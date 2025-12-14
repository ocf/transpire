# transpire

Transpire (/tɹænˈspaɪ̯ɚ/) is a Kubernetes config generation tool designed by and for the Open Computing Facility. If you’re wondering why we wanted to build our own thing, check out the History document.

## Design Goals

Here’s what we wanted out of transpire...

- All non-secret configurations and values should live transparently in Git.
  - This includes Kubernetes resources, and configuration for our own apps.
  - People before us at the OCF opted to throw the entire configuration file into a secret store if it contained any secret values, which is a little annoying if you don’t have access to secrets, and also bad for security because it means more people need access to secrets.
- Secrets are stored securely
  - Can create Kubernetes secrets, and template secrets into application configuration
  - Can automatically generate certain types of secrets (CA Certs, random strings)
- Minimize YAML
  - We don’t like writing YAML very much.
  - Writing YAML tends to result in config being copied around from one project to the next - warts and (now-unnecessary) workarounds included - which makes it hard to change things across the whole organization at once
    - e.g. what to do when you want to change how secrets are injected, and every single project has copy-pasted (sometimes with modifications!) the old method into its own YAML file?
- Support Helm charts
  - We should be able to get any helm chart from a repository
  - We should be able to arbitrarily modify any Helm chart
- Support any other reasonable method of distributing Kubernetes manifests
  - Also known as “HTTP(s) URLs and checksums”

## Usage

Transpire is still rapidly changing and is not (quite) ready for others to use. You will need to read source code.

## Testing

Run `uv run pytest -q`
