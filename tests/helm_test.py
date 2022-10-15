# import pytest

from transpire.helm import build_chart  # , build_chart_from_versions


class HelmTest:
    def test_no_values(self):
        """build a helm chart with no values"""
        chart = build_chart(
            repo_url="https://helm.cilium.io/",
            chart_name="cilium",
            name="cilium",
            version="v1.12.2",
        )
        assert len(chart) > 0

    def test_chart_version_not_exist(self):
        """build a helm chart with a version that doesn't exist"""
        build_chart(
            repo_url="https://helm.cilium.io/",
            chart_name="cilium",
            name="cilium",
            # Cilium authors can push a chart to break our tests!
            # but I think that's fine...
            version="v0.1.doesntexist-ocf-pytest",
        )

    def test_chart_repo_not_exist(self):
        """build a helm chart with a repo that doesn't exist"""
        ...

    def test_chart_chart_not_exist(self):
        """build a helm chart with a chart that doesn't exist"""
        ...

    def test_with_values(self):
        """build a helm chart with a values file"""
        ...

    def test_from_versions(self):
        """build a helm chart from a values object"""
        ...
