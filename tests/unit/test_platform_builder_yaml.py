from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_BUILDER_YAML
from qililab.platforms import PlatformBuilderYAML

from .utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="platform_builder_yaml")
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_platform_builder_yaml(mock_load: MagicMock):
    """Return PlatformBuilderYAML instance with loaded platform."""
    filepath = Path(__file__).parent.parent.parent / "examples" / "all_platform.yml"
    PLATFORM_BUILDER_YAML.build_from_yaml(filepath=str(filepath))
    mock_load.assert_called()
    return PLATFORM_BUILDER_YAML


class TestPlatformBuilderDB:
    """Unit tests checking the PlatformBuilderDB attributes and methods."""

    def test_build_raises_attribute_error(self):
        """Test build method raises attribute error."""
        platform_builder = PlatformBuilderYAML()
        with pytest.raises(AttributeError):
            platform_builder.build(platform_name="platform_0")

    def test_load_bus_item_settings_raises_value_error(self, platform_builder_yaml: PlatformBuilderYAML):
        """Test _load_bus_item_settings method raises value error."""
        platform_builder_yaml.yaml_buses[0] = platform_builder_yaml.yaml_buses[1]  # change sensitive data
        with pytest.raises(ValueError):
            platform_builder_yaml.build(platform_name="platform_0")
