from transpire.dsl import emit, helm

name = "cilium"


def objects():
    chart = helm.build_chart(
        repo_url="https://helm.cilium.io/",
        chart_name="cilium",
        name="cilium",
        version="v1.12.2",
    )

    emit(chart)
