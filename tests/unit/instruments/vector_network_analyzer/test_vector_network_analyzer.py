"""Test for the VectorNetworkAnalyzer class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.agilent.e5071b_vna import E5071B
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.typings.enums import Parameter, VNAScatteringParameters, VNATriggerModes
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


class TestVectorNetworkAnalyzer:
    """Unit tests checking the VectorNetworkAnalyzer methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.POWER, -15.0),
            (Parameter.FREQUENCY_SPAN, 6.4e-3),
            (Parameter.FREQUENCY_CENTER, 8.5e-3),
            (Parameter.FREQUENCY_START, 27.5),
            (Parameter.FREQUENCY_STOP, 40.5),
            (Parameter.IF_BANDWIDTH, 50.0),
            (Parameter.DEVICE_TIMEOUT, 100.0),
            (Parameter.ELECTRICAL_DELAY, 0.0),
        ],
    )
    def test_setup_method_value_flt(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with float value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, float)
        e5080b.setup(parameter, value)
        if parameter == Parameter.POWER:
            assert e5080b.power == value
        if parameter == Parameter.FREQUENCY_SPAN:
            assert e5080b.frequency_span == value
        if parameter == Parameter.FREQUENCY_CENTER:
            assert e5080b.frequency_center == value
        if parameter == Parameter.FREQUENCY_START:
            assert e5080b.frequency_start == value
        if parameter == Parameter.FREQUENCY_STOP:
            assert e5080b.frequency_stop == value
        if parameter == Parameter.IF_BANDWIDTH:
            assert e5080b.if_bandwidth == value
        if parameter == Parameter.DEVICE_TIMEOUT:
            assert e5080b.device_timeout == value
        if parameter == Parameter.ELECTRICAL_DELAY:
            assert e5080b.electrical_delay == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, 0.34),
            (Parameter.VOLTAGE, -20.1),
        ],
    )
    def test_setup_method_flt_raises_exception(self, parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect float parameter"""
        with pytest.raises(ParameterNotFound):
            e5080b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.TRIGGER_MODE, "INT"),
            (Parameter.SCATTERING_PARAMETER, "S21"),
        ],
    )
    def test_setup_method_value_str(self, parameter: Parameter, value, e5071b: E5071B):
        """Test the setup method with str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        e5071b.setup(parameter, value)
        if parameter == Parameter.TRIGGER_MODE:
            assert e5071b.trigger_mode == VNATriggerModes(value)
        if parameter == Parameter.SCATTERING_PARAMETER:
            assert e5071b.scattering_parameter == VNAScatteringParameters(value)

    @pytest.mark.parametrize(
        "value",
        [
            "S221",
            "s11",
        ],
    )
    def test_setup_scattering_value_raises_exception(self, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect str value"""
        assert isinstance(value, str)
        with pytest.raises(ValueError):
            e5071b.scattering_parameter = value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, "foo"),
            (Parameter.VOLTAGE, "bar"),
        ],
    )
    def test_setup_method_str_raises_exception(self, parameter, value, e5071b: E5071B):
        """Test the setup method raises exception with incorrect str parameter"""
        with pytest.raises(ParameterNotFound):
            e5071b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value", [(Parameter.AVERAGING_ENABLED, True), (Parameter.AVERAGING_ENABLED, False)]
    )
    def test_setup_method_value_bool(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with bool value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, bool)
        e5080b.setup(parameter, value)
        if parameter == Parameter.AVERAGING_ENABLED:
            assert e5080b.averaging_enabled == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, True),
            (Parameter.VOLTAGE, False),
        ],
    )
    def test_setup_method_bool_raises_exception(self, parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect bool parameter"""
        with pytest.raises(ParameterNotFound):
            e5080b.setup(parameter, value)

    @pytest.mark.parametrize("parameter, value", [(Parameter.NUMBER_POINTS, 100), (Parameter.NUMBER_AVERAGES, 4)])
    def test_setup_method_value_int(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with int value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, int)
        e5080b.setup(parameter, value)
        if parameter == Parameter.NUMBER_POINTS:
            assert e5080b.number_points == value
        if parameter == Parameter.NUMBER_AVERAGES:
            assert e5080b.number_averages == value

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, 0),
            (Parameter.VOLTAGE, -20),
        ],
    )
    def test_setup_method_int_raises_exception(self, parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect int parameter"""
        with pytest.raises(ParameterNotFound):
            e5080b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SCATTERING_PARAMETER, ["S221"]),
            (Parameter.SCATTERING_PARAMETER, {}),
        ],
    )
    def test_setup_method_raises_exception(self, parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect value type"""
        with pytest.raises(ParameterNotFound):
            e5080b.setup(parameter, value)

    def test_to_dict_method(self, e5080b_no_device: E5080B):
        """Test the dict method"""
        assert isinstance(e5080b_no_device.to_dict(), dict)

    def test_initial_setup_method(self, e5080b: E5080B):
        """Test the initial setup method"""
        e5080b.initial_setup()
        e5080b.device.initial_setup.assert_called()

    def test_reset_method(self, e5080b: E5080B):
        """Test the reset method"""
        e5080b.reset()
        e5080b.device.reset.assert_called()

    def test_turn_on_method(self, e5080b: E5080B):
        """Test turn on method"""
        e5080b.turn_on()
        e5080b.device.send_command.assert_called_with(command=":OUTP", arg="ON")

    def test_turn_off_method(self, e5080b: E5080B):
        """Test turn off method"""
        e5080b.turn_off()
        e5080b.device.send_command.assert_called_with(command=":OUTP", arg="OFF")

    @pytest.mark.parametrize("command", [":SENS1:AVER:CLE", "SENS1:AVER:COUN 3"])
    def test_send_command_method(self, command: str, e5080b: E5080B):
        """Test the send command method"""
        assert isinstance(command, str)
        e5080b.send_command(command)
        e5080b.device.send_command.assert_called_with(command=command, arg="")

    @pytest.mark.parametrize("query", [":SENS1:SWE:MODE?"])
    def test_send_query_method(self, query: str, e5080b: E5080B):
        """Test the send query method"""
        assert isinstance(query, str)
        e5080b.send_query(query)
        e5080b.device.send_query.assert_called_with(query)

    @pytest.mark.parametrize("query", ["SENS:X?", "CALC1:MEAS1:DATA:SDAT?"])
    def test_send_binary_query_method(self, query: str, e5080b: E5080B):
        """Test the send binary query method"""
        assert isinstance(query, str)
        e5080b.send_binary_query(query)
        e5080b.device.send_binary_query.assert_called_with(query)

    def test_read_method(self, e5080b: E5080B):
        """Test the read method"""
        e5080b.read()
        e5080b.device.read.assert_called()

    def test_read_raw_method(self, e5080b: E5080B):
        """Test the read method"""
        e5080b.read_raw()
        e5080b.device.read_raw.assert_called()

    @pytest.mark.parametrize(
        "state, command, arg", [(True, "SENS1:AVER:STAT", "ON"), (False, "SENS1:AVER:STAT", "OFF")]
    )
    def test_average_state_method(self, state, command, arg, e5080b: E5080B):
        """Test the auxiliary private method average state"""
        e5080b._average_state(state)
        e5080b.device.send_command.assert_called_with(command=command, arg=arg)

    def test_average_count_method(self, e5080b: E5080B):
        """Set the average count"""
        e5080b._average_count(1, 1)  # Have to know if you can select which one was called
        e5080b.device.send_command.assert_called()

    def test_autoscale_method(self, e5080b: E5080B):
        """Test the autoscale method"""
        e5080b.autoscale()
        e5080b.device.send_command.assert_called_with(command="DISP:WIND:TRAC:Y:AUTO", arg="")

    def test_power_property(self, e5080b_no_device: E5080B):
        """Test power property."""
        assert hasattr(e5080b_no_device, "power")
        assert e5080b_no_device.power == e5080b_no_device.settings.power

    def test_scattering_parameter_property(self, e5080b_no_device: E5080B):
        """Test the scattering parametter property"""
        assert hasattr(e5080b_no_device, "scattering_parameter")
        assert e5080b_no_device.scattering_parameter == e5080b_no_device.settings.scattering_parameter

    def test_frequency_span_property(self, e5080b_no_device: E5080B):
        """Test the frequency span property"""
        assert hasattr(e5080b_no_device, "frequency_span")
        assert e5080b_no_device.frequency_span == e5080b_no_device.settings.frequency_span

    def test_frequency_center_property(self, e5080b_no_device: E5080B):
        """Test the frequency center property"""
        assert hasattr(e5080b_no_device, "frequency_center")
        assert e5080b_no_device.frequency_center == e5080b_no_device.settings.frequency_center

    def test_frequency_start_property(self, e5080b_no_device: E5080B):
        """Test the frequency start property"""
        assert hasattr(e5080b_no_device, "frequency_start")
        assert e5080b_no_device.frequency_start == e5080b_no_device.settings.frequency_start

    def test_frequency_stop_property(self, e5080b_no_device: E5080B):
        """Test the frequency stop property"""
        assert hasattr(e5080b_no_device, "frequency_stop")
        assert e5080b_no_device.frequency_stop == e5080b_no_device.settings.frequency_stop

    def test_if_bandwidth_property(self, e5080b_no_device: E5080B):
        """Test the if bandwidth property"""
        assert hasattr(e5080b_no_device, "if_bandwidth")
        assert e5080b_no_device.if_bandwidth == e5080b_no_device.settings.if_bandwidth

    def test_averaging_enabled_property(self, e5080b_no_device: E5080B):
        """Test the averaging enabled property"""
        assert hasattr(e5080b_no_device, "averaging_enabled")
        assert e5080b_no_device.averaging_enabled == e5080b_no_device.settings.averaging_enabled

    def test_number_averages_propertyy(self, e5080b_no_device: E5080B):
        """Test the number of averages property"""
        assert hasattr(e5080b_no_device, "number_averages")
        assert e5080b_no_device.number_averages == e5080b_no_device.settings.number_averages

    def test_trigger_mode_property(self, e5080b_no_device: E5080B):
        """Test the trigger mode property"""
        assert hasattr(e5080b_no_device, "trigger_mode")
        assert e5080b_no_device.trigger_mode == e5080b_no_device.settings.trigger_mode

    def test_number_points_property(self, e5080b_no_device: E5080B):
        """Test the number points property"""
        assert hasattr(e5080b_no_device, "number_points")
        assert e5080b_no_device.number_points == e5080b_no_device.settings.number_points

    def test_device_timeout_property(self, e5080b_no_device: E5080B):
        """Test the device timeout property"""
        assert hasattr(e5080b_no_device, "device_timeout")
        assert e5080b_no_device.device_timeout == e5080b_no_device.settings.device_timeout

    def test_electrical_delay_property(self, e5080b_no_device: E5080B):
        """Test the electrical delay property"""
        assert hasattr(e5080b_no_device, "electrical_delay")
        assert e5080b_no_device.electrical_delay == e5080b_no_device.settings.electrical_delay


class TestVectorNetworkAnalyzerDriver:
    """Test for the driver class at typings"""

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_post_init_method(self, mock_resource_manager):
        """Test the postinit function from the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.__post_init__()
        assert vna_driver.driver == mock_resource

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_initial_setup_method(self, mock_resource_manager):
        """Test the initial setup method of the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.initial_setup()
        vna_driver.driver.write.assert_called()

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_reset_method(self, mock_resource_manager):
        """Test the reset method of the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.reset()
        vna_driver.driver.write.assert_called_with("SYST:PRES; *OPC?")

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_send_command(self, mock_resource_manager):
        """Test the send command method of the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.send_command("SENS1:AVER:COUN", "3")
        vna_driver.driver.write.assert_called_with("SENS1:AVER:COUN 3")

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_send_query_method(self, mock_resource_manager):
        """Test the send query method of the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.send_query(":SENS1:SWE:MODE?")
        vna_driver.driver.query.assert_called_with(":SENS1:SWE:MODE?")

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_send_binary_query_method(self, mock_resource_manager):
        """Test the send binary query method of the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.send_binary_query("CALC1:MEAS1:DATA:SDAT?")
        vna_driver.driver.query_binary_values.assert_called_with("CALC1:MEAS1:DATA:SDAT?")

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_set_timeout_method(self, mock_resource_manager):
        """Test the set timeout method of the driver"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.set_timeout(200)
        assert vna_driver.timeout == 200

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_read_method(self, mock_resource_manager):
        """Test the read method to directly from the device"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.read()
        vna_driver.driver.read.assert_called()

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_read_raw_method(self, mock_resource_manager):
        """Test the read method to directly from the device"""
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_driver = VectorNetworkAnalyzerDriver("foo", "bar")
        vna_driver.read_raw()
        vna_driver.driver.read_raw.assert_called()
