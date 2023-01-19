from typing import Any

import pytest

from transpire.surgery import delve, edit_manifests, make_edit_manifest, shelve


class TestDelve:
    def test_basic_functionality(self) -> None:
        val = object()
        obj = {"a": {"b": {"c": val}, "d": True}}
        assert delve(obj, ("a", "b", "c")) is val

    def test_returns_none_on_nonexistent_key(self) -> None:
        obj = {"a": {"b": {"c": "foo"}, "d": True}}
        assert delve(obj, ("a", "b", "nonexistent")) is None


class TestShelve:
    def test_basic_functionality(self) -> None:
        obj = {"a": {"b": {"c": "foo"}, "d": True}}
        expected = {"a": {"b": {"c": "bar"}, "d": True}}
        assert shelve(obj, ("a", "b", "c"), "bar") == expected
        assert obj == expected

    def test_create_key(self) -> None:
        obj = {"a": {"c": "d"}}
        expected = {"a": {"c": "d", "foo": "bar"}}
        assert shelve(obj, ("a", "foo"), "bar") == expected
        assert obj == expected

    def test_parent_creation(self) -> None:
        obj: dict[str, Any] = {}
        expected = {"a": {"b": {"c": "bar"}}}
        assert shelve(obj, ("a", "b", "c"), "bar", create_parents=True) == expected
        assert obj == expected

    def test_missing_segment(self) -> None:
        obj = {"a": {"c": "d"}}
        key = "foo"
        with pytest.raises(KeyError, match=key):
            shelve(obj, ("a", key, "junk"), "junk")

    def test_empty_path(self) -> None:
        obj: dict[str, Any] = {}
        expected = "foo"
        assert shelve(obj, [], expected) == expected


class TestEditManifest:
    def make_manifest(self, apiVersion, kind, name) -> dict:
        return {
            "apiVersion": apiVersion,
            "kind": kind,
            "metadata": {"name": name},
        }

    def test_basic(self) -> None:
        const = lambda v: lambda x: v  # noqa: E731

        manifests = [
            self.make_manifest("v1", "Service", "svc1"),
            self.make_manifest("v1", "Service", "svc2"),
            self.make_manifest("networking.k8s.io/v1", "Ingress", "ingress1"),
            self.make_manifest("networking.k8s.io/v1", "Ingress", "ingress2"),
        ]
        edited = edit_manifests(
            {
                ("Service", "svc1"): const("svc1"),
                ("Ingress", "ingress1"): const("ingress1"),
            },
            manifests,
        )
        assert edited == [
            "svc1",
            self.make_manifest("v1", "Service", "svc2"),
            "ingress1",
            self.make_manifest("networking.k8s.io/v1", "Ingress", "ingress2"),
        ]

    def test_unapplied_edit(self) -> None:
        id = lambda x: x  # noqa: E731

        manifests = [
            self.make_manifest("v1", "Service", "name1"),
            self.make_manifest("v1", "Secret", "name2"),
            self.make_manifest("extensions/v1beta1", "Ingress", "name3"),
        ]
        with pytest.raises(
            RuntimeError, match=r"Some edits were not applied:.*Service.*name2"
        ):
            edit_manifests({("Service", "name2"): id}, manifests)
        with pytest.raises(
            RuntimeError, match=r"Some edits were not applied:.*Ingress.*name1"
        ):
            edit_manifests({("Ingress", "name1"): id}, manifests)
        with pytest.raises(
            RuntimeError,
            match=r"Some edits were not applied:.*networking\.k8s\.io/v1.*Ingress.*name3",
        ):
            edit_manifests(
                {(("networking.k8s.io/v1", "Ingress"), "name3"): id}, manifests
            )


class TestMakeEditManifest:
    def test_basic(self) -> None:
        obj = {"a": {"b": {"c": "foo"}, "d": 1}}
        expected = {"a": {"b": {"c": "bar"}, "d": 2, "new": "value"}}
        edit = make_edit_manifest(
            {
                ("a", "b", "c"): "bar",
                ("a", "d"): 2,
                ("a", "new"): "value",
            }
        )
        assert edit(obj) == expected
        assert obj == expected

    def test_with_edit_manifests(self) -> None:
        manifests = [
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "svc-1",
                    "annotations": {"ocf.io/test": "yes"},
                },
                "spec": {"dummy": "foo"},
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "svc-2",
                    "annotations": {"ocf.io/test": "yes"},
                },
                "spec": {"dummy": "foo"},
            },
        ]
        expected = [
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "svc-1",
                    "annotations": {"ocf.io/test": "no"},
                },
                "spec": {"dummy": "bar"},
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "svc-2",
                    "annotations": {"ocf.io/test": "yes"},
                },
                "spec": {"dummy": "foo"},
            },
        ]
        assert (
            edit_manifests(
                {
                    ("Service", "svc-1"): make_edit_manifest(
                        {
                            ("metadata", "annotations", "ocf.io/test"): "no",
                            ("spec", "dummy"): "bar",
                        }
                    ),
                },
                manifests,
            )
            == expected
        )
