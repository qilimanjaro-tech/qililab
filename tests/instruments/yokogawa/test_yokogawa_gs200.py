"""Tests for the SGS100A class."""
from unittest.mock import MagicMock

import pytest

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.yokogawa.gs200 import GS200
from qililab.typings.enums import Parameter, SourceMode


@pytest.fixture(name="yokogawa_gs200")
def fixture_yokogawa_gs200():
    """Return connected instance of GS200 class"""
    yokogawa_gs200_current = GS200({
        "alias": "yokogawa_current",
        Parameter.SOURCE_MODE.value: "current",
        Parameter.CURRENT.value: [0.5],
        Parameter.VOLTAGE.value: [0.0],
        Parameter.SPAN.value: ["200mA"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        "dacs": [0],
    })
    yokogawa_gs200_current.device = MagicMock()
    yokogawa_gs200_current.device.mock_add_spec(["current", "voltage", "source_mode", "current_range", "voltage_range", "ramp_current", "ramp_voltage", "on", "off"])
    return yokogawa_gs200_current


@pytest.fixture(name="yokogawa_gs200_voltage")
def fixture_yokogawa_gs200_voltage():
    """Return connected instance of GS200 class"""
    yokogawa_gs200_voltage = GS200({
        "alias": "yokogawa_current",
        Parameter.SOURCE_MODE.value: "voltage",
        Parameter.CURRENT.value: [0.0],
        Parameter.VOLTAGE.value: [0.5],
        Parameter.SPAN.value: ["1V"],
        Parameter.RAMPING_ENABLED.value: [True],
        Parameter.RAMPING_RATE.value: [0.01],
        "dacs": [0],
    })
    yokogawa_gs200_voltage.device = MagicMock()
    yokogawa_gs200_voltage.device.mock_add_spec(["current", "voltage", "source_mode", "current_range", "voltage_range", "ramp_current", "ramp_voltage", "on", "off"])
    return yokogawa_gs200_voltage


class TestYokogawaGS200:
    """Unit tests checking the GS200 attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            (Parameter.CURRENT, 0.5),
            (Parameter.VOLTAGE, 0.0),
            (Parameter.RAMPING_ENABLED, True),
            (Parameter.RAMPING_RATE, 0.01),
            (Parameter.SOURCE_MODE, SourceMode.CURRENT),
            (Parameter.SPAN, "200mA"),
        ],
    )
    def test_get_parameter_method(self, parameter: Parameter, expected_value, yokogawa_gs200: GS200):
        """Test the set_parameter method with float value"""
        value = yokogawa_gs200.get_parameter(parameter)
        assert value == expected_value

    @pytest.mark.parametrize(
        "parameter, expected_value",
        [
            (Parameter.CURRENT, 0.0),
            (Parameter.VOLTAGE, 0.5),
            (Parameter.RAMPING_ENABLED, True),
            (Parameter.RAMPING_RATE, 0.01),
            (Parameter.SOURCE_MODE, SourceMode.VOLTAGE),
            (Parameter.SPAN, "1V"),
        ],
    )
    def test_get_parameter_method_voltage(self, parameter: Parameter, expected_value, yokogawa_gs200_voltage: GS200):
        """Test the set_parameter method with float value"""
        value = yokogawa_gs200_voltage.get_parameter(parameter)
        assert value == expected_value

    @pytest.mark.parametrize("parameter", [Parameter.MAX_CURRENT, Parameter.GAIN])
    def test_get_parameter_method_raises_exception(self, parameter: Parameter, yokogawa_gs200: GS200):
        """Test the setup method with float value raises an exception with wrong parameters"""
        with pytest.raises(ParameterNotFound):
            yokogawa_gs200.get_parameter(parameter)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, -0.001),
            (Parameter.CURRENT, 0.0005),
            (Parameter.VOLTAGE, 0.001),
            (Parameter.VOLTAGE, 0.5),
            (Parameter.RAMPING_ENABLED, True),
            (Parameter.RAMPING_ENABLED, False),
            (Parameter.RAMPING_RATE, 0.05),
            (Parameter.SOURCE_MODE, SourceMode.CURRENT),
            (Parameter.SOURCE_MODE, SourceMode.VOLTAGE),
            (Parameter.SPAN, "100mA"),
        ],
    )
    def test_set_parameter_method(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the set_parameter method with float value"""
        yokogawa_gs200.set_parameter(parameter, value)
        if parameter == Parameter.SOURCE_MODE:
            assert yokogawa_gs200.source_mode == SourceMode(value)
        if parameter == Parameter.CURRENT:
            assert yokogawa_gs200.current == value
        if parameter == Parameter.VOLTAGE:
            assert yokogawa_gs200.voltage == value
        if parameter == Parameter.RAMPING_ENABLED:
            assert yokogawa_gs200.ramping_enabled == value
        if parameter == Parameter.RAMPING_RATE:
            assert yokogawa_gs200.ramping_rate == value
        if parameter == Parameter.SPAN:
            assert yokogawa_gs200.span == value

    @pytest.mark.parametrize("parameter, value", [(Parameter.MAX_CURRENT, 0.001), (Parameter.GAIN, 0.0005)])
    def test_set_parameter_method_raises_exception(self, parameter: Parameter, value, yokogawa_gs200: GS200):
        """Test the setup method with float value raises an exception with wrong parameters"""
        with pytest.raises(ParameterNotFound):
            yokogawa_gs200.set_parameter(parameter, value)

    def test_to_dict_method(self, yokogawa_gs200: GS200):
        """Test the dict method"""
        assert isinstance(yokogawa_gs200.to_dict(), dict)

    def test_turn_on_method(self, yokogawa_gs200: GS200):
        """Test start method"""
        yokogawa_gs200.turn_on()
        yokogawa_gs200.device.on.assert_called()

    def test_turn_off_method(self, yokogawa_gs200: GS200):
        """Test stop method"""
        yokogawa_gs200.turn_off()
        yokogawa_gs200.device.off.assert_called()

    @pytest.mark.parametrize("yokogawa_fixture", ["yokogawa_gs200", "yokogawa_gs200_voltage"])
    def test_initial_setup_method(self, yokogawa_fixture: str, request):
        """Test the initial setup method"""
        yokogawa_gs200 = request.getfixturevalue(yokogawa_fixture)
        yokogawa_gs200.initial_setup()
        yokogawa_gs200.device.source_mode.assert_called()
        assert yokogawa_gs200.source_mode == yokogawa_gs200.settings.source_mode
        assert yokogawa_gs200.span == yokogawa_gs200.settings.span[0]
        assert yokogawa_gs200.ramping_rate == yokogawa_gs200.settings.ramp_rate[0]
        assert yokogawa_gs200.ramping_enabled == yokogawa_gs200.settings.ramping_enabled[0]
        if yokogawa_gs200.source_mode == SourceMode.CURRENT:
            yokogawa_gs200.device.current_range.assert_called()
            if yokogawa_gs200.ramping_enabled:
                yokogawa_gs200.device.ramp_current.assert_called()
            else:
                yokogawa_gs200.device.current.assert_called()
            assert yokogawa_gs200.current == yokogawa_gs200.settings.current[0]
        else:
            yokogawa_gs200.device.voltage_range.assert_called()
            if yokogawa_gs200.ramping_enabled:
                yokogawa_gs200.device.ramp_voltage.assert_called()
            else:
                yokogawa_gs200.device.voltage.assert_called()
            assert yokogawa_gs200.voltage == yokogawa_gs200.settings.voltage[0]

    def test_ramping_enabled_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "ramping_enabled")
        assert yokogawa_gs200.ramping_enabled == yokogawa_gs200.settings.ramping_enabled[0]
        yokogawa_gs200.ramping_enabled = False
        assert not yokogawa_gs200.ramping_enabled

    def test_ramping_rate_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "ramping_rate")
        assert yokogawa_gs200.ramping_rate == yokogawa_gs200.settings.ramp_rate[0]
        yokogawa_gs200.ramping_rate = 0.05
        assert yokogawa_gs200.ramping_rate == 0.05

    def test_current_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "current")
        assert yokogawa_gs200.current == yokogawa_gs200.settings.current[0]
        yokogawa_gs200.current = 0.01
        yokogawa_gs200.device.ramp_current.assert_called()
        assert yokogawa_gs200.current == 0.01
        yokogawa_gs200.ramping_enabled = False
        yokogawa_gs200.current = 0.0
        yokogawa_gs200.device.current.assert_called()
        assert yokogawa_gs200.current == 0.0

    def test_voltage_property(self, yokogawa_gs200: GS200):
        """Test the voltage property"""
        assert hasattr(yokogawa_gs200, "voltage")
        assert yokogawa_gs200.voltage == yokogawa_gs200.settings.voltage[0]
        yokogawa_gs200.voltage = 0.01
        yokogawa_gs200.device.ramp_voltage.assert_called()
        assert yokogawa_gs200.voltage == 0.01
        yokogawa_gs200.ramping_enabled = False
        yokogawa_gs200.voltage = 0.0
        yokogawa_gs200.device.voltage.assert_called()
        assert yokogawa_gs200.voltage == 0.0

    def test_source_mode_property(self, yokogawa_gs200: GS200):
        """Test the source mode property"""
        assert hasattr(yokogawa_gs200, "source_mode")
        yokogawa_gs200.source_mode = SourceMode.VOLTAGE
        yokogawa_gs200.device.source_mode.assert_called()
        assert yokogawa_gs200.source_mode == SourceMode.VOLTAGE
        yokogawa_gs200.source_mode = SourceMode.CURRENT
        yokogawa_gs200.device.source_mode.assert_called()
        assert yokogawa_gs200.source_mode == SourceMode.CURRENT

    def test_span_property(self, yokogawa_gs200: GS200):
        """Test the span property"""
        assert hasattr(yokogawa_gs200, "span")
        assert yokogawa_gs200.span == yokogawa_gs200.settings.span[0]
        yokogawa_gs200.span = "1mA"
        yokogawa_gs200.device.current_range.assert_called()
        yokogawa_gs200.source_mode = SourceMode.VOLTAGE
        yokogawa_gs200.span = "1V"
        yokogawa_gs200.device.voltage_range.assert_called()
        assert yokogawa_gs200.span == "1V"
