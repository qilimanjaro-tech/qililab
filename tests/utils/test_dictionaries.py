""" Tests for Dictionaries utilities"""

import pytest

from qililab.utils.dictionaries import merge_dictionaries


@pytest.fixture(name="origin")
def fixture_origin_dictionary() -> dict:
    origin = {
        "should_not_update": {"a": 1, "b": 2, "c": 3},
        "should_update_inner_element_c": {"a": 1, "b": 2, "c": 3},
        "should_update": {},
    }

    return origin


@pytest.fixture(name="new")
def fixture_new_dictionary() -> dict:
    new = {"should_update_inner_element_c": {"c": 100}, "should_update": {"a": 1, "b": 2, "c": 3}}

    return new


class TestDictionaries:
    """Unit tests for utils.dictionaries module"""

    def test_merge_dictionaries(self, origin: dict, new: dict):
        merged = merge_dictionaries(origin, new)

        assert len(merged["should_not_update"]) == 3
        assert merged["should_not_update"]["a"] == 1
        assert merged["should_not_update"]["b"] == 2
        assert merged["should_not_update"]["c"] == 3

        assert len(merged["should_update_inner_element_c"]) == 3
        assert merged["should_update_inner_element_c"]["a"] == 1
        assert merged["should_update_inner_element_c"]["b"] == 2
        assert merged["should_update_inner_element_c"]["c"] == 100

        assert len(merged["should_update"]) == 3
        assert merged["should_update"]["a"] == 1
        assert merged["should_update"]["b"] == 2
        assert merged["should_update"]["c"] == 3
