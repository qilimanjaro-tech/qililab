"""Tests for the Schema class."""
import pytest

from qililab.platform import Platform, Schema
from tests.data import Galadriel
from tests.test_utils import platform_db


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)


@pytest.fixture(name="schema")
def fixture_schema(platform: Platform) -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    return platform.schema


class Testschema:
    """Unit tests checking the Schema attributes and methods."""

    def test_print_schema(self, schema: Schema):
        """Test print schema."""
        print(schema)

    def test_print_instruments(self, schema: Schema):
        """Test print instruments."""
        print(schema.instruments)

    def test_print_chip(self, schema: Schema):
        """Test print chip."""
        print(schema.chip)
