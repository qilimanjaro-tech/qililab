"""Tests for the Platform class."""
from types import NoneType
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_DB
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform import Buses, Platform, Qubit, Resonator, Schema
from qililab.typings import Category

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
        assert platform.num_qubits == 1

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_get_element_method_schema(self, platform: Platform):
        """Test get_element method with schema."""
        assert isinstance(platform.get_element(category=Category.SCHEMA)[0], Schema)

    def test_get_element_method_buses(self, platform: Platform):
        """Test get_element method with buses."""
        assert isinstance(platform.get_element(category=Category.BUSES)[0], Buses)

    def test_get_element_method_unknown(self, platform: Platform):
        """Test get_element method with unknown element."""
        assert isinstance(platform.get_element(category=Category.AWG, id_=6)[0], NoneType)

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.settings, Platform.PlatformSettings)

    def test_schema_instance(self, platform: Platform):
        """Test schema instance."""
        assert isinstance(platform.schema, Schema)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element, bus_idxs = platform.get_element(category=Category.SIGNAL_GENERATOR, id_=0)
        assert isinstance(element, SignalGenerator)
        assert bus_idxs[0] == 0

    def test_bus_0_mixer_instance(self, platform: Platform):
        """Test bus 0 mixer instance."""
        element, bus_idxs = platform.get_element(category=Category.MIXER, id_=0)
        assert isinstance(element, Mixer)
        assert bus_idxs[0] == 0

    def test_bus_1_resonator_instance(self, platform: Platform):
        """Test bus 1 resonator instance."""
        element, bus_idxs = platform.get_element(category=Category.RESONATOR, id_=0)
        assert isinstance(element, Resonator)
        assert bus_idxs[0] == 1

    def test_qubit_0_instance(self, platform: Platform):
        """Test qubit 0 instance."""
        element, bus_idxs = platform.get_element(category=Category.QUBIT, id_=0)
        assert isinstance(element, Qubit)
        assert bus_idxs[0] == 0

    def test_qubit_1_instance(self, platform: Platform):
        """Test qubit 1 instance."""
        element, bus_idxs = platform.get_element(category=Category.QUBIT, id_=1)
        assert isinstance(element, NoneType)
        assert bus_idxs == []

    def test_bus_0_awg_instance(self, platform: Platform):
        """Test bus 0 qubit control instance."""
        element, bus_idxs = platform.get_element(category=Category.AWG, id_=0)
        assert isinstance(element, QubitControl)
        assert bus_idxs[0] == 0

    def test_bus_1_awg_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        element, bus_idxs = platform.get_element(category=Category.AWG, id_=1)
        assert isinstance(element, QubitReadout)
        assert bus_idxs[0] == 1

    @patch("qililab.settings.settings_manager.yaml.dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, platform: Platform):
        """Test PlatformManager dump method."""
        PLATFORM_MANAGER_DB.dump(platform=platform)
        mock_dump.assert_called()
