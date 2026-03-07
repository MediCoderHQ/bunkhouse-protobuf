"""Basic sanity tests for the bunkhouse_protobuf package."""

import importlib


def test_package_importable():
    mod = importlib.import_module("bunkhouse_protobuf")
    assert mod is not None


def test_version_string():
    from bunkhouse_protobuf._version import __version__
    assert isinstance(__version__, str)
    parts = __version__.split(".")
    assert len(parts) == 3, f"Expected semver, got {__version__!r}"
