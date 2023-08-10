"""Tests for the Platform class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab import save_platform
from qililab.chip import Chip, Qubit
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.instrument_controllers import InstrumentControllers
from qililab.instruments import AWG, AWGAnalogDigitalConverter, SignalGenerator
from qililab.instruments.instruments import Instruments
from qililab.platform import Bus, Buses, Platform
from qililab.settings import Runcard
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import InstrumentName
from qililab.typings.yaml_type import yaml
from tests.data import Galadriel
from tests.test_utils import platform_db, platform_yaml


@pytest.mark.parametrize("runcard", [Runcard(**Galadriel.runcard)])
class TestPlatformInitialization:
    """Unit tests for the Platform class initialization"""

    def test_init_method(self, runcard):
        """Test initialization of the class"""
        platform = Platform(runcard=runcard)

        assert platform.transpilation_settings == runcard.transpilation_settings
        assert isinstance(platform.transpilation_settings, Runcard.TranspilationSettings)
        assert isinstance(platform.instruments, Instruments)
        assert isinstance(platform.instrument_controllers, InstrumentControllers)
        assert isinstance(platform.chip, Chip)
        assert isinstance(platform.buses, Buses)
        assert platform.connection is None
        assert platform._connected_to_instruments is False


@pytest.mark.parametrize("platform", [platform_db(runcard=Galadriel.runcard), platform_yaml(runcard=Galadriel.runcard)])
class TestPlatform:
    """Unit tests checking the Platform class."""

    def test_id_property(self, platform: Platform):
        """Test id property."""
        assert platform.id_ == platform.transpilation_settings.id_

    def test_name_property(self, platform: Platform):
        """Test name property."""
        assert platform.name == platform.transpilation_settings.name

    def test_category_property(self, platform: Platform):
        """Test category property."""
        assert platform.category == platform.transpilation_settings.category

    def test_num_qubits_property(self, platform: Platform):
        """Test num_qubits property."""
        assert platform.num_qubits == platform.chip.num_qubits

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_get_element_method_unknown_returns_none(self, platform: Platform):
        """Test get_element method with unknown element."""
        element = platform.get_element(alias="ABC")
        assert element is None

    def test_get_element_with_gate(self, platform: Platform):
        """Test the get_element method with a gate alias."""
        for qubit, gate_settings_list in platform.transpilation_settings.gates.items():
            for gate_settings in gate_settings_list:
                alias = f"{gate_settings.name}{qubit}" if isinstance(qubit, tuple) else f"{gate_settings.name}({qubit})"
                gate = platform.get_element(alias=alias)
                assert isinstance(gate, Runcard.TranspilationSettings.GateSettings)
                assert gate.name == gate_settings.name

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_transpilation_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.transpilation_settings, Runcard.TranspilationSettings)

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

    def test_get_bus_by_qubit_index(self, platform: Platform):
        """Test get_bus_by_qubit_index method."""
        _, control_bus, readout_bus = platform.get_bus_by_qubit_index(0)
        assert isinstance(control_bus, Bus)
        assert isinstance(readout_bus, Bus)
        assert not isinstance(control_bus.system_control, ReadoutSystemControl)
        assert isinstance(readout_bus.system_control, ReadoutSystemControl)

    def test_get_bus_by_qubit_index_raises_error(self, platform: Platform):
        """Test that the get_bus_by_qubit_index method raises an error when there is no bus connected to the port
        of the given qubit."""
        platform.buses[0].settings.port = 100
        with pytest.raises(ValueError, match="Could not find buses for qubit 0 connected to the ports"):
            platform.get_bus_by_qubit_index(0)

    @pytest.mark.parametrize("alias", ["drive_line_bus", "feedline_input_output_bus", "foobar"])
    def test_get_bus_by_alias(self, platform: Platform, alias):
        """Test get_bus_by_alias method"""
        bus = platform.get_bus_by_alias(alias)
        if alias == "foobar":
            assert bus is None
        if bus is not None:
            assert bus in platform.buses

    def test_print_platform(self, platform: Platform):
        """Test print platform."""
        assert str(platform) == str(yaml.dump(platform.to_dict(), sort_keys=False))

    # I'm leaving this test here, because there is no test_instruments.py, but should be moved there when created
    def test_print_instruments(self, platform: Platform):
        """Test print instruments."""
        assert str(platform.instruments) == str(yaml.dump(platform.instruments._short_dict(), sort_keys=False))
