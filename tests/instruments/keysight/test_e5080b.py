"""Tests for the E5080B class."""
import io
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.keysight import E5080B
from qililab.typings.enums import Parameter
from ruamel.yaml import YAML

from qililab.instruments import ParameterNotFound
from qililab.constants import CONNECTION, INSTRUMENTCONTROLLER, RUNCARD
from qililab.instrument_controllers.keysight import E5080BController
from qililab.platform import Platform
from qililab.typings.enums import ConnectionName, InstrumentControllerName, Parameter, VNAAverageModes, VNAFormatBorder, VNAScatteringParameters, VNASweepModes, VNASweepTypes

from tests.data import SauronVNA
from tests.test_utils import build_platform

@pytest.fixture(name="e5080b")
def fixture_e5080b() -> E5080B:
    """Fixture that returns an instance of a dummy keysight E5080B."""
    e5080b = E5080B(
        {
            "alias": "vna",
        }
    )
    e5080b.device = MagicMock()
    return e5080b

@pytest.fixture(name="e5080b_mocked_binary_return")
def fixture_e5080b_mocked_binary_return() -> E5080B:
    """Fixture that returns an instance of a dummy keysight E5080B."""
    e5080b = E5080B(
        {
            "alias": "vna",
        }
    )
    e5080b.device = MagicMock()
    e5080b.device.ask.return_value = "256"
    return e5080b

@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=SauronVNA.runcard)

@pytest.fixture(name="e5080b_controller")
def fixture_e5080b_controller(platform: Platform):
    """Return an instance of VectorNetworkAnalyzer controller class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b_controller)
    settings.pop("name")
    return E5080BController(settings=settings, loaded_instruments=platform.instruments)

@pytest.fixture(name="e5080b_no_device")
def fixture_e5080b_no_device():
    """Return an instance of VectorNetworkAnalyzer class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b)
    settings.pop("name")
    return E5080B(settings=settings)

@pytest.fixture(name="e5080b_settings")
def fixture_e5080b_settings():
    """Fixture that returns an instance of a dummy VNA."""
    return {
        RUNCARD.NAME: InstrumentControllerName.KEYSIGHT_E5080B,
        RUNCARD.ALIAS: "keysight_e5080b",
        INSTRUMENTCONTROLLER.CONNECTION: {
            RUNCARD.NAME: ConnectionName.TCP_IP.value,
            CONNECTION.ADDRESS: "169.254.150.105",
        },
        INSTRUMENTCONTROLLER.MODULES: [
            {
                "alias": "keysight_e5080b",
                "slot_id": 0,
            }
        ],
    }

@pytest.fixture(name="e5080b_controller_mock")
@patch(
    "qililab.instrument_controllers.keysight.keysight_E5080B_vna_controller",
    autospec=True,
)
def fixture_e5080b_controller_mock(mock_device: MagicMock, e5080b_controller: E5080BController):
    """Return connected instance of VectorNetworkAnalyzer class"""
    mock_controller = MagicMock(spec=E5080BController)
    mock_controller.connect.return_value = None
    e5080b_controller = mock_device.return_value
    return e5080b_controller.modules[0]


class TestE5080B:
    """Unit tests checking the E5080B attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SOURCE_POWER, 0.01),
            (Parameter.FREQUENCY_START, 1e6),
            (Parameter.FREQUENCY_STOP, 8e9),
            (Parameter.FREQUENCY_CENTER, 4e9),
            (Parameter.FREQUENCY_SPAN, 7.99e9),
            (Parameter.CW_FREQUENCY, 4e9),
            (Parameter.NUMBER_POINTS, 201),
            (Parameter.IF_BANDWIDTH, 1e3),
            (Parameter.SWEEP_TYPE, VNASweepTypes.LIN),
            (Parameter.SWEEP_MODE, VNASweepModes.CONT),
            (Parameter.SCATTERING_PARAMETER, VNAScatteringParameters.S21),
            (Parameter.AVERAGES_ENABLED, True),
            (Parameter.NUMBER_AVERAGES, 16),
            (Parameter.AVERAGES_MODE, VNAAverageModes.POIN),
            (Parameter.FORMAT_BORDER, VNAFormatBorder.SWAP),
            (Parameter.RF_ON, False),
        ],
    )
    def test_set_parameter_method(
        self,
        e5080b: E5080B,
        parameter: Parameter,
        value: float,
    ):
        """Test setup parameter"""
        e5080b.set_parameter(parameter=parameter, value=value)
        if parameter == Parameter.SOURCE_POWER:
            assert e5080b.settings.source_power == value
        if parameter == Parameter.FREQUENCY_START:
            assert e5080b.settings.frequency_start == value
        if parameter == Parameter.FREQUENCY_STOP:
            assert e5080b.settings.frequency_stop == value
        if parameter == Parameter.FREQUENCY_CENTER:
            assert e5080b.settings.frequency_center == value
        if parameter == Parameter.FREQUENCY_SPAN:
            assert e5080b.settings.frequency_span == value
        if parameter == Parameter.CW_FREQUENCY:
            assert e5080b.settings.cw_frequency == value
        if parameter == Parameter.NUMBER_POINTS:
            assert e5080b.settings.number_points == value
        if parameter == Parameter.IF_BANDWIDTH:
            assert e5080b.settings.if_bandwidth == value
        if parameter == Parameter.SWEEP_TYPE:
            assert e5080b.settings.sweep_type == value
        if parameter == Parameter.SWEEP_MODE:
            assert e5080b.settings.sweep_mode == value
        if parameter == Parameter.SCATTERING_PARAMETER:
            assert e5080b.settings.scattering_parameter == value
        if parameter == Parameter.AVERAGES_ENABLED:
            assert e5080b.settings.averages_enabled == value
        if parameter == Parameter.NUMBER_AVERAGES:
            assert e5080b.settings.number_averages == value
        if parameter == Parameter.AVERAGES_MODE:
            assert e5080b.settings.averages_mode == value
        if parameter == Parameter.RF_ON:
            assert e5080b.settings.rf_on == value
        if parameter == Parameter.FORMAT_BORDER:
            assert e5080b.settings.format_border == value

    def test__clear_averages(
            self,
            e5080b: E5080B,
        ):
        e5080b.clear_averages()


    def test_set_parameter_method_raises_error(self, e5080b: E5080B):
        """Test setup method"""
        with pytest.raises(ParameterNotFound):
            e5080b.set_parameter(parameter=Parameter.BUS_FREQUENCY, value=123)

    @pytest.mark.parametrize(
        "parameter_get, expected_value",
        [
            (Parameter.SOURCE_POWER, 0.01),
            (Parameter.FREQUENCY_START, 1e6),
            (Parameter.FREQUENCY_STOP, 8e9),
        ],
    )

    def test_get_parameter_method_raises_error(self, e5080b: E5080B, parameter_get: Parameter, expected_value: float):
        """Test setup method"""
        with pytest.raises(ParameterNotFound):
            e5080b.set_parameter(parameter=parameter_get, value=expected_value)
            e5080b.get_parameter(parameter=Parameter.BUS_FREQUENCY)


    @pytest.mark.parametrize(
        "parameter_get, expected_value",
        [
           (Parameter.SOURCE_POWER, 0.01),
            (Parameter.FREQUENCY_START, 1e6),
            (Parameter.FREQUENCY_STOP, 8e9),
            (Parameter.FREQUENCY_CENTER, 4e9),
            (Parameter.FREQUENCY_SPAN, 7.99e9),
            (Parameter.CW_FREQUENCY, 4e9),
            (Parameter.NUMBER_POINTS, 201),
            (Parameter.IF_BANDWIDTH, 1e3),
            (Parameter.SWEEP_TYPE, VNASweepTypes.LIN),
            (Parameter.SWEEP_MODE, VNASweepModes.CONT),
            (Parameter.SCATTERING_PARAMETER, VNAScatteringParameters.S21),
            (Parameter.AVERAGES_ENABLED, True),
            (Parameter.NUMBER_AVERAGES, 16),
            (Parameter.AVERAGES_MODE, VNAAverageModes.POIN),
            (Parameter.FORMAT_BORDER, VNAFormatBorder.SWAP),
            (Parameter.RF_ON, False),
        ],
    )
    def test_get_parameter_method(
        self,
        e5080b: E5080B,
        parameter_get: Parameter,
        expected_value: float,
    ):
        """Test get_parameter method"""
        e5080b.set_parameter(parameter=parameter_get, value=expected_value)
        value = e5080b.get_parameter(parameter=parameter_get)
        assert value == expected_value


    def test_error_raises_when_no_modules(self, platform: Platform, e5080b_settings):
        """Test that ensures an error raises when there is no module specifyed

        Args:
            platform (Platform): Platform
        """
        e5080b_settings[INSTRUMENTCONTROLLER.MODULES] = []
        name = e5080b_settings.pop(RUNCARD.NAME)
        with pytest.raises(ValueError, match=f"The {name.value} Instrument Controller requires at least ONE module."):
            E5080BController(settings=e5080b_settings, loaded_instruments=platform.instruments)

    def test_print_instrument_controllers(self, platform: Platform):
        """Test print instruments."""
        instr_cont = platform.instrument_controllers
        assert str(instr_cont) == str(YAML().dump(instr_cont.to_dict(), io.BytesIO()))

    def test_to_dict_method(self, e5080b_no_device: E5080B):
        """Test the dict method"""
        assert isinstance(e5080b_no_device.to_dict(), dict)

    def test_turn_on_method(self, e5080b: E5080B):
        """Test turn_on method"""
        e5080b.turn_on()

    def test_turn_off_method(self, e5080b: E5080B):
        """Test turn_off method"""
        e5080b.turn_off()

    def test_reset_method(self, e5080b: E5080B):
        """Test reset method"""
        e5080b.reset()

    def test_get_trace(self, e5080b: E5080B):
        e5080b._get_trace()

    def test_pre_measurement(self, e5080b: E5080B):
        e5080b._pre_measurement(power = 10)

    def test_pre_measurement_with_nb_avg(self, e5080b: E5080B):
        e5080b.set_parameter(Parameter.NUMBER_AVERAGES,10)
        e5080b._pre_measurement(power = 10)

    def test_start_measurement(self, e5080b: E5080B):
        e5080b._start_measurement()

    def test_release(self, e5080b: E5080B):
        e5080b.release()

    def test_acquire_result(self, e5080b: E5080B):
        timeout = 0.001
        power = 0
        with pytest.raises(TimeoutError, match=f"Timeout of {timeout} ms exceeded while waiting for averaging to complete."):
            e5080b.acquire_result(power, timeout)

    def test_wait_for_averaging(self, e5080b: E5080B):
        timeout = 0.001
        with pytest.raises(TimeoutError, match=f"Timeout of {timeout} ms exceeded while waiting for averaging to complete."):
            e5080b._wait_for_averaging(timeout)

    def test_wait_for_averaging_no_timeout(self, e5080b_mocked_binary_return: E5080B):
        timeout = 0.001
        e5080b_mocked_binary_return._wait_for_averaging(timeout)

    def test_read_tracedata_success(self, e5080b: E5080B):
        timeout=100
        power=0
        with patch.object(e5080b, '_wait_for_averaging', return_value=None) as mock_wait_for_averaging, \
            patch.object(e5080b, '_get_trace', return_value='fake_trace_data') as mock_get_trace, \
            patch.object(e5080b, 'release') as mock_release:
            
            # Call the method
            trace = e5080b.read_tracedata(power,timeout)
            
            # Assert the trace is as expected and release was called
            assert trace == 'fake_trace_data'
            mock_release.assert_called_once()

    def test_read_tracedata_timeout(self, e5080b: E5080B):
        timeout = 0.001
        power = 0
        with pytest.raises(TimeoutError, match=f"Timeout of {timeout} ms exceeded while waiting for averaging to complete."):
            e5080b.read_tracedata(power, timeout)

    def test_read_tracedata_averages_enabled_timeout(self, e5080b: E5080B):
        e5080b.set_parameter(Parameter.AVERAGES_ENABLED,True)
        timeout = 0.001
        power = 0
        with pytest.raises(TimeoutError, match=f"Timeout of {timeout} ms exceeded while waiting for averaging to complete."):
            e5080b.read_tracedata(power, timeout)

    def test_get_frequencies_method(self, e5080b: E5080B):
        """Test the get frequencies method"""
        e5080b.get_frequencies()

    def test_init_controller(self, e5080b_controller_mock: E5080BController):
        e5080b_controller_mock.initial_setup()
        e5080b_controller_mock._initialize_device()


    @pytest.mark.parametrize(
        "parameter, value, method",
        [
            (Parameter.FREQUENCY_START, 1e6, "start_freq"),
            (Parameter.FREQUENCY_STOP, 8e9, "stop_freq"),
            (Parameter.FREQUENCY_CENTER, 4e9, "center_freq"),
            (Parameter.FREQUENCY_SPAN, 7.99e9, "span"),
            (Parameter.AVERAGES_MODE, VNAAverageModes.SWE, "averages_mode"),
            (Parameter.NUMBER_AVERAGES, 7.99e9, "averages_count"),
            (Parameter.SWEEP_TYPE, VNASweepTypes.CW, "sweep_type"),
            (Parameter.CW_FREQUENCY, 1e6, "cw"),
            (Parameter.SWEEP_MODE, VNASweepModes.CONT, "sweep_mode"),
            (Parameter.NUMBER_POINTS, 140, "points"),
            (Parameter.IF_BANDWIDTH, 1e6, "if_bandwidth"),
            (Parameter.SCATTERING_PARAMETER, VNAScatteringParameters.S22, "scattering_parameter"),
            (Parameter.FORMAT_BORDER, VNAFormatBorder.NORM, "format_border"),
        ],
    )
    def test_initial_setup_with_parameter(self, e5080b: E5080B, parameter: Parameter, value: float, method: str):
        """Test the initial setup when sweep_type is not 'SEGM'."""
        e5080b.reset()
        e5080b.set_parameter(parameter=parameter, value=value)
        e5080b.set_parameter(Parameter.SWEEP_TYPE, "cw")
        e5080b.device.reset_mock()
        e5080b.initial_setup()
        getattr(e5080b.device, method).assert_called_once_with(value)

    @patch("qililab.instrument_controllers.keysight.keysight_E5080B_vna_controller.KeysightE5080B", autospec=True)
    @pytest.mark.parametrize("controller_alias", ["keysight_e5080b"])
    def test_initial_setup(self, device_mock: MagicMock, platform: Platform, controller_alias: str):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)
        device_mock.return_value.opc = MagicMock()
        device_mock.return_value.format_data = MagicMock()
        device_mock.return_value.cls = MagicMock()
        device_mock.return_value.source_power = MagicMock()
        device_mock.return_value.sweep_type = MagicMock()
        device_mock.return_value.sweep_mode = MagicMock()
        device_mock.return_value.points = MagicMock()
        device_mock.return_value.if_bandwidth = MagicMock()
        device_mock.return_value.scattering_parameter = MagicMock()
        device_mock.return_value.rf_on = MagicMock()
        device_mock.return_value.averages_enabled = MagicMock()
        device_mock.return_value.start_freq = MagicMock()
        device_mock.return_value.center_freq = MagicMock()
        device_mock.return_value.stop_freq = MagicMock()
        device_mock.return_value.span = MagicMock()
        device_mock.return_value.cw = MagicMock()
        device_mock.return_value.averages_count = MagicMock()
        device_mock.return_value.averages_mode = MagicMock()
        device_mock.return_value.format_border = MagicMock()
        controller_instance.connect()
        controller_instance.initial_setup()

    @patch("qililab.instrument_controllers.keysight.keysight_E5080B_vna_controller.KeysightE5080B", autospec=True)
    @pytest.mark.parametrize("controller_alias", ["keysight_e5080b"])
    def test_initialize_device(self, device_mock: MagicMock, platform: Platform, controller_alias: str):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)

        controller_instance._initialize_device()

        name = f"{controller_instance.name.value}_{controller_instance.alias}"
        address = (
            f"TCPIP::{controller_instance.address}::INSTR"
        )
        device_mock.assert_called_once_with(name=name, address=address, visalib="@py")

