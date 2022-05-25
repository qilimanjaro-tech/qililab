"""Tests for the Schema class."""
import pytest

from qililab.platform import Schema
from qililab.typings import SchemaDrawOptions


class Testschema:
    """Unit tests checking the Schema attributes and methods."""

    def test_draw_method_print(self, schema: Schema):
        """Test schema schema draw method."""
        schema.draw(options=SchemaDrawOptions.PRINT)

    def test_draw_method__file(self, schema: Schema):
        """Test schema schema draw method raise error."""
        with pytest.raises(NotImplementedError):
            schema.draw(options=SchemaDrawOptions.FILE)
