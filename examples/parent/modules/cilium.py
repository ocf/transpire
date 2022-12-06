from transpire import helm

name = "cilium"


def objects():
    yield from helm.build_chart(
        repo_url="https://helm.cilium.io/",
        chart_name="cilium",
        name="cilium",
        version="v1.12.2",
    )
