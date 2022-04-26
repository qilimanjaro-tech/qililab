import pytest

from qililab.platform import Schema
from qililab.typings import SchemaDrawOptions

from ...data import MockedSettingsHashTable


@pytest.fixture(name="schema")
def fixture_schema() -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    schema_settings = MockedSettingsHashTable.get("schema")

    return Schema(settings=schema_settings)


class Testschema:
    """Unit tests checking the Schema attributes and methods."""

    def test_id_property(self, schema: Schema):
        """Test id property."""
        assert schema.id_ == schema.settings.id_

    def test_name_property(self, schema: Schema):
        """Test name property."""
        assert schema.name == schema.settings.name

    def test_category_property(self, schema: Schema):
        """Test name property."""
        assert schema.category == schema.settings.category

    def test_settings_instance(self, schema: Schema):
        """Test schema schema settings instance."""
        assert isinstance(schema.settings, Schema.SchemaSettings)

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
