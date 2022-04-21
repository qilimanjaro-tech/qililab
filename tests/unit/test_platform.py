from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_BUILDER_DB
from qililab.buses import Buses
from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platforms import Platform
from qililab.resonator import Resonator
from qililab.schema import Schema
from qililab.settings import PlatformSettings, SchemaSettings

from .utils.side_effect import yaml_safe_load_side_effect


@pytest.fixture(name="platform")
@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
def fixture_platform_builder_db(mock_load: MagicMock):
    """Return PlatformBuilderDB instance with loaded platform."""
    PLATFORM_BUILDER_DB.build(platform_name="platform_0")
    mock_load.assert_called()
    return PLATFORM_BUILDER_DB.platform


class TestPlatform:
    """Unit tests checking the Platform attributes and methods."""

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == "platform"

    def test_platform_str_method(self, platform: Platform):
        """Test platform __str__ method."""
        assert str(platform) == platform.name

    def test_platform_settings_instance(self, platform: Platform):
        """Test platform settings instance."""
        assert isinstance(platform.settings, PlatformSettings)

    def test_platform_schema_instance(self, platform: Platform):
        """Test platform schema instance."""
        assert isinstance(platform.schema, Schema)

    def test_platform_schema_settings_instance(self, platform: Platform):
        """Test platform schema settings instance."""
        assert isinstance(platform.schema.settings, SchemaSettings)

    def test_platform_schema_num_buses(self, platform: Platform):
        """Test platform schema num_buses."""
        assert platform.schema.num_buses == 3

    def test_platform_schema_draw_method(self, platform: Platform):
        """Test platform schema draw method."""
        platform.schema.draw()

    def test_platform_schema_asdict_method(self, platform: Platform):
        """Test platform schema asdict method."""
        assert isinstance(platform.schema.asdict(), dict)

    def test_platform_buses_instance(self, platform: Platform):
        """Test platform buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_platform_buses_asdict_method(self, platform: Platform):
        """Test platform buses asdict method."""
        assert isinstance(platform.buses.asdict(), list)

    def test_platform_bus_1_signal_generator_instance(self, platform: Platform):
        """Test platform bus 1 signal generator instance."""
        assert isinstance(platform.buses.buses[0].signal_generator, SignalGenerator)

    def test_platform_bus_1_mixer_instance(self, platform: Platform):
        """Test platform bus 1 mixer instance."""
        assert isinstance(platform.buses.buses[0].mixer, Mixer)

    def test_platform_bus_1_resonator_instance(self, platform: Platform):
        """Test platform bus 1 resonator instance."""
        assert isinstance(platform.buses.buses[0].resonator, Resonator)

    @patch("qililab.settings.settings_manager.yaml.safe_dump")
    def test_platform_dump_method(self, mock_dump: MagicMock, platform: Platform):
        """Test platform dump method."""
        platform.dump()
        mock_dump.assert_called()
