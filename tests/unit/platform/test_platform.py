"""Tests for the Platform class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab import save_platform
from qililab.chip import Qubit
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.instruments import AWG, AWGAnalogDigitalConverter, SignalGenerator
from qililab.platform import Buses, Platform, Schema
from qililab.settings import RuncardSchema
from qililab.typings.enums import InstrumentName

from ...conftest import platform_db, platform_yaml


@pytest.mark.parametrize("platform", [platform_db(), platform_yaml()])
class TestPlatform:
    """Unit tests checking the Platform attributes and methods."""

    def test_id_property(self, platform: Platform):
        """Test id property."""
        assert platform.id_ == platform.settings.id_

    def test_name_property(self, platform: Platform):
        """Test name property."""
        assert platform.name == platform.settings.name

    def test_category_property(self, platform: Platform):
        """Test category property."""
        assert platform.category == platform.settings.category

    def test_num_qubits_property(self, platform: Platform):
        """Test num_qubits property."""
        assert platform.num_qubits == platform.chip.num_qubits

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_get_element_method_unknown_raises_error(self, platform: Platform):
        """Test get_element method with unknown element."""
        with pytest.raises(ValueError):
            platform.get_element(alias="ABC")

    def test_get_element_with_gate(self, platform: Platform):
        """Test the get_element method with a gate alias."""
        gate = platform.get_element(alias="M")
        assert isinstance(gate, RuncardSchema.PlatformSettings.GateSettings)
        assert gate.name == "M"

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.settings, RuncardSchema.PlatformSettings)

    def test_schema_instance(self, platform: Platform):
        """Test schema instance."""
        assert isinstance(platform.schema, Schema)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element = platform.get_element(alias="rs_0")
        assert isinstance(element, SignalGenerator)

    def test_qubit_0_instance(self, platform: Platform):
        """Test qubit 1 instance."""
        element = platform.get_element(alias="qubit")
        assert isinstance(element, Qubit)

    def test_bus_0_awg_instance(self, platform: Platform):
        """Test bus 0 qubit control instance."""
        element = platform.get_element(alias=InstrumentName.QBLOX_QCM.value)
        assert isinstance(element, AWG)

    def test_bus_1_awg_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        element = platform.get_element(alias=InstrumentName.QBLOX_QRM.value)
        assert isinstance(element, AWGAnalogDigitalConverter)

    @patch("qililab.platform.platform_manager.yaml.dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, platform: Platform):
        """Test PlatformManager dump method."""
        save_platform(platform=platform)
        with pytest.raises(NotImplementedError):
            save_platform(platform=platform, database=True)
        mock_dump.assert_called()
