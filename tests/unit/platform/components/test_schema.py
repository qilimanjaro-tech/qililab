from unittest.mock import patch

import pytest

from qililab.platform import PLATFORM_MANAGER_DB, Schema
from qililab.typings import SchemaDrawOptions

from ...utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="schema")
def fixture_schema() -> Schema:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")
        mock_load.assert_called()
    return platform.schema


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
