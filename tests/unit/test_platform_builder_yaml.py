from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_BUILDER_YAML
from qililab.buses import Buses
from qililab.platforms import Platform, PlatformBuilderYAML
from qililab.schema import Schema
from qililab.settings import PlatformSettings

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

    def test_platform_attribute(self, platform_builder_yaml: PlatformBuilderYAML):
        """Test platform attribute."""
        assert isinstance(platform_builder_yaml.platform, Platform)

    def test_platform_settings(self, platform_builder_yaml: PlatformBuilderYAML):
        """Test platform settings."""
        assert isinstance(platform_builder_yaml.platform.settings, PlatformSettings)

    def test_platform_schema(self, platform_builder_yaml: PlatformBuilderYAML):
        """Test platform schema."""
        assert isinstance(platform_builder_yaml.platform.schema, Schema)

    def test_platform_buses(self, platform_builder_yaml: PlatformBuilderYAML):
        """Test platform buses."""
        assert isinstance(platform_builder_yaml.platform.buses, Buses)
