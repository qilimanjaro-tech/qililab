import importlib
import importlib.metadata as importlib_metadata
import types

import pytest

from qililab._optionals import (
    ImportedFeature,
    OptionalDependencyError,
    OptionalFeature,
    Symbol,
    import_optional_dependencies,
)


def test_import_optional_dependencies_missing(monkeypatch):
    feature = OptionalFeature(
        name="example",
        dependencies=["pkg-one"],
        symbols=[
            Symbol(path="fake.module", name="do_work"),
            Symbol(path="fake.module", name="Special", kind="class"),
        ],
    )

    def fake_version(_dist: str) -> str:
        raise importlib_metadata.PackageNotFoundError

    monkeypatch.setattr(importlib_metadata, "version", fake_version)

    imported = import_optional_dependencies(feature)
    assert isinstance(imported, ImportedFeature)
    assert imported.name == "example"

    stub_func = imported.symbols["do_work"]
    assert stub_func.__name__ == "do_work"
    with pytest.raises(OptionalDependencyError) as excinfo:
        stub_func(1, kw="value")
    assert "installing the 'example' optional feature" in str(excinfo.value)

    stub_class = imported.symbols["Special"]
    assert stub_class.__doc__ == "Stub for missing optional dependency 'example'."
    with pytest.raises(OptionalDependencyError):
        stub_class("arg")

    instance = object.__new__(stub_class)
    with pytest.raises(OptionalDependencyError):
        instance.some_attr
    with pytest.raises(OptionalDependencyError):
        instance()


def test_import_optional_dependencies_success(monkeypatch):
    feature = OptionalFeature(
        name="example",
        dependencies=["pkg-one", "pkg-two"],
        symbols=[
            Symbol(path="fake.module", name="do_work"),
            Symbol(path="fake.module", name="Special", kind="class"),
        ],
    )

    def fake_version(_dist: str) -> str:
        return "0.1.0"

    real_module = types.ModuleType("fake.module")

    def do_work():
        return "done"

    class Special:
        """Test double."""

    real_module.do_work = do_work
    real_module.Special = Special

    imported_paths: list[str] = []

    def fake_import(path: str):
        imported_paths.append(path)
        return real_module

    monkeypatch.setattr(importlib_metadata, "version", fake_version)
    monkeypatch.setattr(importlib, "import_module", fake_import)

    imported = import_optional_dependencies(feature)
    assert imported.symbols["do_work"] is do_work
    assert imported.symbols["Special"] is Special
    assert imported_paths == ["fake.module", "fake.module"]

    assert isinstance(imported, ImportedFeature)
    assert imported.name == "example"
