import pytest

import transpire
from transpire.helm import build_chart


class TestHelm:
    def test_no_values(self):
        """build a helm chart with no values"""
        transpire.set_app_name("test")
        chart = build_chart(
            repo_url="https://helm.cilium.io/",
            chart_name="cilium",
            name="cilium",
            version="v1.12.2",
        )
        assert len(chart) > 0

    def test_chart_version_not_exist(self):
        """build a helm chart with a version that doesn't exist"""
        with pytest.raises(Exception):
            transpire.set_app_name("test")
            build_chart(
                repo_url="https://helm.cilium.io/",
                chart_name="cilium",
                name="cilium",
                # Cilium authors can push a chart to break our tests!
                # but I think that's fine...
                version="v0.1.doesntexist-ocf-pytest",
            )

    def test_with_empty_values(self):
        """build a helm chart with an empty values file"""
        transpire.set_app_name("test")
        chart = build_chart(
            repo_url="https://helm.cilium.io/",
            chart_name="cilium",
            name="cilium",
            version="v1.12.2",
            values={},
        )
        assert len(chart) > 0

    def test_from_versions(self):
        """build a helm chart from a versions object"""
        # TODO: Write test!
        ...

    def test_with_real_values(self):
        """build a helm chart with some real values"""
        # TODO: Write test!
        ...
