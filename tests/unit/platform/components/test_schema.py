"""Tests for the Schema class."""
from qililab.platform import Schema


class Testschema:
    """Unit tests checking the Schema attributes and methods."""

    def test_print_schema(self, schema: Schema):
        """Test print schema."""
        print(schema)

    def test_print_instruments(self, schema: Schema):
        """Test print instruments."""
        print(schema.instruments)
