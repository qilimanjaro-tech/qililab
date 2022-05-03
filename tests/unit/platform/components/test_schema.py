import pytest

from qililab.platform import PLATFORM_MANAGER_YAML, Schema
from qililab.typings import Category, SchemaDrawOptions

from ...data import MockedSettingsHashTable


@pytest.fixture(name="schema")
def fixture_schema() -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    schema_settings = MockedSettingsHashTable.get(Category.SCHEMA.value)

    return PLATFORM_MANAGER_YAML.build_schema(schema_settings=schema_settings)


class Testschema:
    """Unit tests checking the Schema attributes and methods."""

    def test_asdict_method(self, schema: Schema):
        """Test schema schema asdict method."""
        assert isinstance(schema.to_dict(), dict)

    def test_draw_method_print(self, schema: Schema):
        """Test schema schema draw method."""
        schema.draw(options=SchemaDrawOptions.PRINT)

    def test_draw_method__file(self, schema: Schema):
        """Test schema schema draw method raise error."""
        with pytest.raises(NotImplementedError):
            schema.draw(options=SchemaDrawOptions.FILE)
