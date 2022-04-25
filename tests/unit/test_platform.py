from pathlib import Path
from types import NoneType
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_DB, PLATFORM_MANAGER_YAML
from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform import Platform
from qililab.platform.components import Buses, Qubit, Resonator, Schema

from .utils.side_effect import yaml_safe_load_side_effect


def platform_db():
    """Return PlatformBuilderDB instance with loaded platform."""
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")
        mock_load.assert_called()
    return platform


def platform_yaml():
    """Return PlatformBuilderYAML instance with loaded platform."""
    filepath = Path(__file__).parent.parent.parent / "examples" / "all_platform.yml"
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_YAML.build_from_yaml(filepath=str(filepath))
        mock_load.assert_called()
    return platform


@pytest.mark.parametrize("platform", [platform_db(), platform_yaml()])
class TestPlatform:
    """Unit tests checking the Platform attributes and methods."""

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == "platform"

    def test_platform_settings_instance(self, platform: Platform):
        """Test platform settings instance."""
        assert isinstance(platform.settings, Platform.PlatformSettings)

    def test_platform_schema_instance(self, platform: Platform):
        """Test platform schema instance."""
        assert isinstance(platform.schema, Schema)

    def test_platform_schema_settings_instance(self, platform: Platform):
        """Test platform schema settings instance."""
        assert isinstance(platform.schema.settings, Schema.SchemaSettings)

    def test_platform_schema_draw_method(self, platform: Platform):
        """Test platform schema draw method."""
        platform.schema.draw()

    def test_platform_schema_asdict_method(self, platform: Platform):
        """Test platform schema asdict method."""
        assert isinstance(platform.schema.to_dict(), dict)

    def test_platform_buses_instance(self, platform: Platform):
        """Test platform buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_platform_bus_0_signal_generator_instance(self, platform: Platform):
        """Test platform bus 0 signal generator instance."""
        assert isinstance(platform.buses.buses[0].signal_generator, SignalGenerator)

    def test_platform_bus_0_mixer_instance(self, platform: Platform):
        """Test platform bus 0 mixer instance."""
        assert isinstance(platform.buses.buses[0].mixer, Mixer)

    def test_platform_bus_0_resonator_instance(self, platform: Platform):
        """Test platform bus 0 resonator instance."""
        assert isinstance(platform.buses.buses[0].resonator, Resonator)

    def test_platform_bus_0_resonator_qubit_0_instance(self, platform: Platform):
        """Test platform bus 0 resonator qubit 0 instance."""
        assert isinstance(platform.buses.buses[0].resonator.settings.qubits[0], Qubit)

    def test_platform_bus_0_qubit_control_instance(self, platform: Platform):
        """Test platform bus 0 qubit control instance."""
        assert isinstance(platform.buses.buses[0].qubit_control, QubitControl)

    def test_platform_bus_1_qubit_control_instance(self, platform: Platform):
        """Test platform bus 1 qubit control instance."""
        assert isinstance(platform.buses.buses[1].qubit_control, NoneType)

    def test_platform_bus_0_qubit_readout_instance(self, platform: Platform):
        """Test platform bus 0 qubit readout instance."""
        assert isinstance(platform.buses.buses[0].qubit_readout, NoneType)

    def test_platform_bus_1_qubit_readout_instance(self, platform: Platform):
        """Test platform bus 1 qubit readout instance."""
        assert isinstance(platform.buses.buses[1].qubit_readout, QubitReadout)

    @patch("qililab.settings.settings_manager.yaml.safe_dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, platform: Platform):
        """Test platform dump method."""
        PLATFORM_MANAGER_DB.dump(platform=platform)
        mock_dump.assert_called()
