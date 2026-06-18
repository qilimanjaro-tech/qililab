# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""QILILAB-04 regression tests: DB-sourced result paths must be canonicalised and,
when an allow-list of roots is configured, confined before they are opened."""

import os
from types import SimpleNamespace

import pytest

from qililab.result.database import database_measurements as dbm


def _settings(allowed_roots=""):
    return SimpleNamespace(experiment_results_allowed_roots=allowed_roots)


def test_validated_result_path_default_canonicalises(tmp_path, monkeypatch):
    """With no allow-list configured, the path is canonicalised and returned."""
    monkeypatch.setattr(dbm, "get_settings", lambda: _settings(""))
    p = tmp_path / "r.h5"
    p.write_text("")
    assert dbm._validated_result_path(str(p)) == os.path.realpath(str(p))


@pytest.mark.parametrize("bad", ["", None, 123])
def test_validated_result_path_rejects_invalid(bad, monkeypatch):
    monkeypatch.setattr(dbm, "get_settings", lambda: _settings(""))
    with pytest.raises(ValueError):
        dbm._validated_result_path(bad)


def test_validated_result_path_confines_to_allowed_roots(tmp_path, monkeypatch):
    """When allow-list roots are configured, paths outside them are rejected."""
    root = tmp_path / "results"
    root.mkdir()
    inside = root / "a.h5"
    inside.write_text("")
    outside = tmp_path / "evil.h5"
    outside.write_text("")
    sibling = tmp_path / "results-evil"
    sibling.mkdir()
    sibling_file = sibling / "b.h5"
    sibling_file.write_text("")

    monkeypatch.setattr(dbm, "get_settings", lambda: _settings(str(root)))

    assert dbm._validated_result_path(str(inside)) == os.path.realpath(str(inside))
    with pytest.raises(ValueError):
        dbm._validated_result_path(str(outside))
    with pytest.raises(ValueError):
        dbm._validated_result_path(str(sibling_file))  # component-aware: not under "results"
