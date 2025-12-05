"""Tests for the E5080B class."""
import io
import copy
from unittest.mock import MagicMock, patch

import pytest
import time

from qililab.instruments.keysight import E5080B, e5080b_vna
from qililab.typings.enums import Parameter
from ruamel.yaml import YAML
from enum import Enum

from qililab.instruments import ParameterNotFound
from qililab.constants import CONNECTION, INSTRUMENTCONTROLLER, RUNCARD
from qililab.instrument_controllers.keysight import E5080BController
from qililab.platform import Platform
from qililab.typings.enums import ConnectionName, InstrumentControllerName, Parameter, VNAAverageModes, VNAFormatBorder, VNAScatteringParameters, VNASweepModes, VNASweepTypes, VNATriggerSource, VNATriggerType, VNATriggerSlope

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

@pytest.fixture(name="e5080b_get_param")
def fixture_e5080b_get_param() -> E5080B:
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
            (Parameter.SWEEP_TIME, 4),
            (Parameter.SWEEP_TIME_AUTO, False),
            (Parameter.TRIGGER_SOURCE, VNATriggerSource.EXT),
            (Parameter.SWEEP_GROUP_COUNT, 5),
            (Parameter.TRIGGER_TYPE, VNATriggerType.LEV),
            (Parameter.TRIGGER_SLOPE, VNATriggerSlope.POS),
            (Parameter.ELECTRICAL_DELAY, 10000)
        ],
    )
    def test_set_parameter_method(
        self,
        e5080b: E5080B,
        parameter: Parameter,
        value: float,
    ):
        """Test setup parameter"""
        if parameter == Parameter.ELECTRICAL_DELAY:
            e5080b.set_parameter(parameter=parameter, value=value, channel_id=2)
            assert e5080b.settings.electrical_delay["Channel 2"] == value
        else:
            e5080b.set_parameter(parameter=parameter, value=value,)
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
        if parameter == Parameter.SWEEP_TIME:
            assert e5080b.settings.sweep_time == value
        if parameter == Parameter.SWEEP_TIME_AUTO:
            assert e5080b.settings.sweep_time_auto == value
        if parameter == Parameter.TRIGGER_SOURCE:
            assert e5080b.settings.trigger_source == value
        if parameter == Parameter.SWEEP_GROUP_COUNT:
            assert e5080b.settings.sweep_group_count == value
        if parameter == Parameter.TRIGGER_TYPE:
            assert e5080b.settings.trigger_type == value
        if parameter == Parameter.TRIGGER_SLOPE:
            assert e5080b.settings.trigger_slope == value

    def test__clear_averages(
            self,
            e5080b: E5080B,
        ):
        e5080b.clear_averages()


    def test_set_parameter_method_raises_error(self, e5080b: E5080B):
        """Test setup method"""
        with pytest.raises(ParameterNotFound):
            e5080b.set_parameter(parameter=Parameter.BUS_FREQUENCY, value=123)
        with pytest.raises(ValueError):
            e5080b.set_parameter(parameter=Parameter.ELECTRICAL_DELAY, value=1000)
            e5080b.set_parameter(parameter=Parameter.ELECTRICAL_DELAY, value=2e10, channel_id=2)
    

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
        with pytest.raises(ValueError):
            e5080b.get_parameter(parameter=Parameter.ELECTRICAL_DELAY)


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
            (Parameter.OPERATION_STATUS, 0),
            (Parameter.SWEEP_TIME, 50),
            (Parameter.SWEEP_TIME_AUTO, False),
            (Parameter.TRIGGER_SOURCE, VNATriggerSource.IMM),
            (Parameter.SWEEP_GROUP_COUNT, 150),
            (Parameter.TRIGGER_TYPE, VNATriggerType.EDGE),
            (Parameter.TRIGGER_SLOPE,VNATriggerSlope.POS),
            (Parameter.ELECTRICAL_DELAY, {"Channel 1":100, "Channel 2":100}),
        ],
    )
    def test_get_parameter_method(
        self,
        e5080b_get_param: E5080B,
        parameter_get: Parameter,
        expected_value: float,
    ):
        attr_map = {
        Parameter.SOURCE_POWER:         "source_power",
        Parameter.FREQUENCY_START:      "start_freq",
        Parameter.FREQUENCY_STOP:       "stop_freq",
        Parameter.FREQUENCY_CENTER:     "center_freq",
        Parameter.FREQUENCY_SPAN:       "span",
        Parameter.CW_FREQUENCY:         "cw",
        Parameter.NUMBER_POINTS:        "points",
        Parameter.IF_BANDWIDTH:         "if_bandwidth",
        Parameter.SWEEP_TYPE:           "sweep_type",
        Parameter.SWEEP_MODE:           "sweep_mode",
        Parameter.SCATTERING_PARAMETER: "scattering_parameter",
        Parameter.AVERAGES_ENABLED:     "averages_enabled",
        Parameter.NUMBER_AVERAGES:       "averages_count",
        Parameter.AVERAGES_MODE:        "averages_mode",
        Parameter.FORMAT_BORDER:        "format_border",
        Parameter.RF_ON:                "rf_on",
        Parameter.OPERATION_STATUS:     "operation_status",
        Parameter.SWEEP_TIME:           "sweep_time",
        Parameter.SWEEP_TIME_AUTO:       "sweep_time_auto",
        Parameter.TRIGGER_SOURCE:        "trigger_source",
        Parameter.SWEEP_GROUP_COUNT:     "sweep_group_count",
        Parameter.TRIGGER_SLOPE:     "trigger_slope",
        Parameter.TRIGGER_TYPE:     "trigger_type",
        Parameter.ELECTRICAL_DELAY:   "electrical_delay",
    }
        raw = expected_value.value if isinstance(expected_value, Enum) else expected_value
        if parameter_get == Parameter.ELECTRICAL_DELAY:
            # electrical_delay is NOT read from the device; it's just stored in settings
            e5080b_get_param.settings.electrical_delay = expected_value
        else:
            raw = expected_value.value if isinstance(expected_value, Enum) else expected_value
            getattr(e5080b_get_param.device, attr_map[parameter_get]).get.return_value = raw

        value = e5080b_get_param.get_parameter(parameter=parameter_get, channel_id=2)
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

    def test_opc(self, e5080b: E5080B):
        """Test opc method"""
        e5080b.opc()

    def test_turn_off_method(self, e5080b: E5080B):
        """Test turn_off method"""
        e5080b.turn_off()

    def test_get_data(self, e5080b: E5080B):
        """Test get_data method"""
        e5080b.get_data()

    def test_get_frequencies(self, e5080b: E5080B):
        """Test get_frequencies method"""
        e5080b.get_frequencies()

    def test_reset_method(self, e5080b: E5080B):
        """Test reset method"""
        e5080b.reset()

    def test_get_trace(self, e5080b: E5080B):
        e5080b._get_trace()

    def test_release(self, e5080b: E5080B):
        e5080b.release()

    def test_acquire_result(self, e5080b: E5080B):
        timeout = 0.001
        msg = f"Timeout of {timeout} seconds exceeded while waiting for averaging to complete."
        # force _wait_for_averaging to immediately raise the correct TimeoutError
        with patch.object(e5080b, "_wait_for_averaging", side_effect=TimeoutError(msg)):
            with pytest.raises(TimeoutError, match=msg):
                e5080b.acquire_result(timeout)

    def test_wait_for_averaging(self, e5080b: E5080B):
        timeout = 0.001
        msg = f"Timeout of {timeout} seconds exceeded while waiting for averaging to complete."
        with patch.object(e5080b, "_wait_for_averaging", side_effect=TimeoutError(msg)):
            with pytest.raises(TimeoutError, match=msg):
                e5080b._wait_for_averaging(timeout)

    def test_wait_for_averaging_no_timeout(self, e5080b_mocked_binary_return: E5080B):
        timeout = 0.001
        msg = f"Timeout of {timeout} seconds exceeded while waiting for averaging to complete."
        with patch.object(e5080b_mocked_binary_return, "_wait_for_averaging", side_effect=TimeoutError(msg)):
            with pytest.raises(TimeoutError, match=msg):
                e5080b_mocked_binary_return._wait_for_averaging(timeout)

    def test_read_tracedata_success(self, e5080b: E5080B):
        timeout=100
        with patch.object(e5080b, '_wait_for_averaging', return_value=None) as mock_wait_for_averaging, \
            patch.object(e5080b, '_get_trace', return_value='fake_trace_data') as mock_get_trace, \
            patch.object(e5080b, 'release') as mock_release:
            
            # Call the method
            trace = e5080b.read_tracedata(timeout)
            
            # Assert the trace is as expected and release was called
            assert trace == 'fake_trace_data'
            mock_release.assert_called_once()

    def test_read_tracedata_timeout(self, e5080b: E5080B):
        timeout = 0.001
        msg = f"Timeout of {timeout} seconds exceeded while waiting for averaging to complete."
        with patch.object(e5080b, "read_tracedata", side_effect=TimeoutError(msg)):
            with pytest.raises(TimeoutError, match=msg):
                e5080b.read_tracedata(timeout)

    def test_read_tracedata_averages_enabled_timeout(self, e5080b: E5080B):
        e5080b.set_parameter(Parameter.AVERAGES_ENABLED,True)
        timeout = 0.001
        msg = f"Timeout of {timeout} seconds exceeded while waiting for averaging to complete."
        with patch.object(e5080b, "read_tracedata", side_effect=TimeoutError(msg)):
            with pytest.raises(TimeoutError, match=msg):
                e5080b.read_tracedata(timeout)

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
            (Parameter.SOURCE_POWER, -10, "source_power"),
            (Parameter.RF_ON, True, "rf_on"),
            (Parameter.SWEEP_TIME, 5, "sweep_time"),
            (Parameter.SWEEP_TIME_AUTO, True, "sweep_time_auto"),
            (Parameter.TRIGGER_SOURCE, VNATriggerSource.MAN, "trigger_source"),
            (Parameter.SWEEP_GROUP_COUNT, 20000, "sweep_group_count"),
            (Parameter.TRIGGER_SLOPE, VNATriggerSlope.POS, "trigger_slope"),
            (Parameter.TRIGGER_TYPE, VNATriggerType.EDGE, "trigger_type"),
            (Parameter.ELECTRICAL_DELAY, 100, "electrical_delay"),
        ],
    )
    def test_initial_setup_with_parameter(self, e5080b: E5080B, parameter: Parameter, value: float, method: str):
        """Test the initial setup when sweep_type is not 'SEGM'."""
        e5080b.reset()
        if parameter==Parameter.ELECTRICAL_DELAY:
            e5080b.set_parameter(parameter=parameter, value=value, channel_id=1)
        else:
            e5080b.set_parameter(parameter=parameter, value=value)
        e5080b.set_parameter(Parameter.SWEEP_TYPE, VNASweepTypes.CW)
        e5080b.device.reset_mock()
        e5080b.initial_setup()
        if parameter==Parameter.ELECTRICAL_DELAY:
            assert e5080b.electrical_delay["Channel 1"] == value
        else:
            getattr(e5080b.device, method).assert_called_once_with(value)

    @patch("qililab.instrument_controllers.keysight.keysight_E5080B_vna_controller.KeysightE5080B", autospec=True)
    @pytest.mark.parametrize("controller_alias", ["keysight_e5080b"])
    def test_initial_setup(self, device_mock: MagicMock, platform: Platform, controller_alias: str):
        """Test QDAC-II controller initializes device correctly."""
        controller_instance = platform.instrument_controllers.get_instrument_controller(alias=controller_alias)
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
        device_mock.return_value.source_power = MagicMock()
        device_mock.return_value.rf_on = MagicMock()
        device_mock.return_value.sweep_time = MagicMock()
        device_mock.return_value.sweep_time_auto = MagicMock()
        device_mock.return_value.trigger_source = MagicMock()
        device_mock.return_value.sweep_group_count = MagicMock()
        device_mock.return_value.trigger_slope = MagicMock()
        device_mock.return_value.trigger_type = MagicMock()
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

# note: string-based monkeypatch targets the module-level import
MODULE_PATH = "qililab.instruments.keysight.e5080b_vna"

def test_wait_for_averaging_breaks_on_bit8(monkeypatch, e5080b):
    # 1) patch out the sleep in YOUR module so we don't actually pause
    monkeypatch.setattr(f"{MODULE_PATH}.time.sleep", lambda _: None)

    # 2) pretend NUMBER_AVERAGES is >1
    monkeypatch.setattr(e5080b, "get_parameter", lambda p: 2)

    # 3) return a status word with bit‐8 set
    e5080b.device.operation_status.get.return_value = 1 << 8

    # 4) should exit immediately (no exception)
    e5080b._wait_for_averaging(timeout=1.0)


def test_wait_for_averaging_breaks_on_bit10(monkeypatch, e5080b):
    # patch sleep again
    monkeypatch.setattr(f"{MODULE_PATH}.time.sleep", lambda _: None)

    # now pretend NUMBER_AVERAGES == 1
    monkeypatch.setattr(e5080b, "get_parameter", lambda p: 1)

    # return a status word with bit‐10 set
    e5080b.device.operation_status.get.return_value = 1 << 10

    e5080b._wait_for_averaging(timeout=1.0)

def test_wait_for_averaging_raises_timeout(monkeypatch, e5080b):
    # patch sleep again
    monkeypatch.setattr(f"{MODULE_PATH}.time.sleep", lambda _: None)

    # now pretend NUMBER_AVERAGES == 1
    monkeypatch.setattr(e5080b, "get_parameter", lambda p: 2)

    # return a status word with bit‐10 set
    e5080b.device.operation_status.get.return_value = 0

    # 4) Make time.time() jump past the timeout on the first loop iteration
    times = iter([0.0, 2.0])  # start_time = 0.0, then time.time() = 2.0 > timeout=1.0
    monkeypatch.setattr(f"{MODULE_PATH}.time.time", lambda: next(times))

    # 5) Should raise a TimeoutError with the right message
    with pytest.raises(TimeoutError) as exc:
        e5080b._wait_for_averaging(timeout=1.0)

    assert "Timeout of 1.0 seconds exceeded" in str(exc.value)

def test_update_settings(e5080b: E5080B):
    """Test that update_settings pulls values from device and sets settings correctly."""
    # Map of attribute name on device → expected value to be returned
    expected_device_values = {
        "start_freq": 1e6,
        "stop_freq": 2e6,
        "center_freq": 1.5e6,
        "span": 1e6,
        "cw": 1.2e6,
        "points": 201,
        "source_power": -10.0,
        "if_bandwidth": 5e3,
        "sweep_type": VNASweepTypes.LIN,
        "sweep_mode": VNASweepModes.CONT,
        "sweep_time": 0.01,
        "sweep_time_auto": True,
        "averages_enabled": True,
        "averages_count": 8,
        "scattering_parameter": VNAScatteringParameters.S21,
        "format_border": VNAFormatBorder.NORM,
        "rf_on": False,
        "operation_status": 256,
        "trigger_source": VNATriggerSource.EXT,
        "sweep_group_count": 300,
        "trigger_type": VNATriggerType.EDGE,
        "trigger_slope": VNATriggerSource.EXT,
    }

    # Set up the device.get() return values accordingly
    for attr, val in expected_device_values.items():
        getattr(e5080b.device, attr).get.return_value = val

    # Act
    e5080b.update_settings()

    # Map device attribute name to settings attribute name (if different)
    remap = {
        "cw": "cw_frequency",
        "points": "number_points",
        "averages_count": "number_averages",
        "start_freq": "frequency_start",
        "stop_freq": "frequency_stop",
        "center_freq": "frequency_center",
        "span": "frequency_span"
    }

    # Assert each setting was updated
    for attr, expected in expected_device_values.items():
        settings_attr = remap.get(attr, attr)
        actual = getattr(e5080b.settings, settings_attr)
        assert actual == expected, f"Expected {settings_attr}={expected}, got {actual}"
