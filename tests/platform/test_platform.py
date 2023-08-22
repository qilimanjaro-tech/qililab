"""Tests for the Platform class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab import save_platform
from qililab.chip import Chip, Qubit
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.drivers.instruments import Instruments as NewInstruments
from qililab.instrument_controllers import InstrumentControllers
from qililab.instruments import AWG, AWGAnalogDigitalConverter, SignalGenerator
from qililab.instruments.instruments import Instruments
from qililab.platform import Bus, Buses, Platform
from qililab.settings import Runcard
from qililab.settings.gate_event_settings import GateEventSettings
from qililab.system_control import ReadoutSystemControl
from qililab.typings.enums import InstrumentName
from qililab.typings.yaml_type import yaml
from tests.data import Galadriel, NewGaladriel
from tests.test_utils import platform_db

@pytest.mark.parametrize("new_runcard", [Runcard(**NewGaladriel.runcard)])
class TestPlatformInitializationNewRuncard:
    """Unit tests for the Platform class initialization using new runcard, instruments and buses"""

    def test_init_method(self, new_runcard):
        """Test initialization of the class"""
        platform = Platform(runcard=new_runcard, new_drivers=True)

        assert platform.name == new_runcard.name
        assert isinstance(platform.name, str)
        assert isinstance(platform.new_instruments, NewInstruments)

@pytest.mark.parametrize("runcard", [Runcard(**Galadriel.runcard)])
class TestPlatformInitialization:
    """Unit tests for the Platform class initialization"""

    def test_init_method(self, runcard):
        """Test initialization of the class"""
        platform = Platform(runcard=runcard)

        assert platform.name == runcard.name
        assert isinstance(platform.name, str)
        assert platform.device_id == runcard.device_id
        assert isinstance(platform.device_id, int)
        assert platform.gates_settings == runcard.gates_settings
        assert isinstance(platform.gates_settings, Runcard.GatesSettings)
        assert isinstance(platform.instruments, Instruments)
        assert isinstance(platform.instrument_controllers, InstrumentControllers)
        assert isinstance(platform.chip, Chip)
        assert isinstance(platform.buses, Buses)
        assert platform.connection is None
        assert platform._connected_to_instruments is False


@pytest.fixture(name="platform")
def fixture_platform():
    return copy.deepcopy(platform_db(Galadriel.runcard))


class TestPlatform:
    """Unit tests checking the Platform class."""

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_get_element_method_unknown_returns_none(self, platform: Platform):
        """Test get_element method with unknown element."""
        element = platform.get_element(alias="ABC")
        assert element is None

    def test_get_element_with_gate(self, platform: Platform):
        """Test the get_element method with a gate alias."""
        gates = platform.gates_settings.gates.keys()
        all(isinstance(event, GateEventSettings) for gate in gates for event in platform.get_element(alias=gate))

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_gates_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.gates_settings, Runcard.GatesSettings)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        element = platform.get_element(alias="rs_0")
        assert isinstance(element, SignalGenerator)

    def test_qubit_0_instance(self, platform: Platform):
        """Test qubit 0 instance."""
        element = platform.get_element(alias="q0")
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
        platform.buses[0].settings.port = 0  # Setting it back to normal to not disrupt future tests

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

    def test_serialization(self, platform: Platform):
        """Test that a serialization of the Platform is possible"""
        runcard_dict = platform.to_dict()
        assert isinstance(runcard_dict, dict)

        new_platform = Platform(runcard=Runcard(**runcard_dict))
        assert isinstance(new_platform, Platform)
        assert str(new_platform) == str(platform)
        assert str(new_platform.name) == str(platform.name)
        assert str(new_platform.device_id) == str(platform.device_id)
        assert str(new_platform.buses) == str(platform.buses)
        assert str(new_platform.chip) == str(platform.chip)
        assert str(new_platform.instruments) == str(platform.instruments)
        assert str(new_platform.instrument_controllers) == str(platform.instrument_controllers)

        new_runcard_dict = new_platform.to_dict()
        assert isinstance(new_runcard_dict, dict)
        assert new_runcard_dict == runcard_dict

        newest_platform = Platform(runcard=Runcard(**new_runcard_dict))
        assert isinstance(newest_platform, Platform)
        assert str(newest_platform) == str(new_platform)
        assert str(newest_platform.name) == str(new_platform.name)
        assert str(newest_platform.device_id) == str(new_platform.device_id)
        assert str(newest_platform.buses) == str(new_platform.buses)
        assert str(newest_platform.chip) == str(new_platform.chip)
        assert str(newest_platform.instruments) == str(new_platform.instruments)
        assert str(newest_platform.instrument_controllers) == str(new_platform.instrument_controllers)
