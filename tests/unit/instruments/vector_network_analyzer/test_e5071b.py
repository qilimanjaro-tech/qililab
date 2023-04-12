"""Test for the VectorNetworkAnalyzer E5071B class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.agilent.e5071b_vna import E5071B
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import Parameter


class TestE5071B:
    """Unit tests checking the VectorNetworkAnalyzer E5071B attributes and methods"""

    @patch("numpy.frombuffer")
    def test_get_data_method(self, mock_frombuffer, e5071b: E5071B):  # sourcery skip: simplify-division
        """Test the get data method"""
        mock_buffer = MagicMock(name="mock_frombuffer")
        mock_frombuffer.return_value = mock_buffer
        e5071b.get_data()
        e5071b.device.send_command.assert_called()
        e5071b.device.read_raw.assert_called()

    @patch("numpy.frombuffer")
    def test_acquire_result_method(self, mock_frombuffer, e5071b: E5071B):
        """Test the acquire result method"""
        mock_buffer = MagicMock(name="mock_frombuffer")
        mock_frombuffer.return_value = mock_buffer
        output = e5071b.acquire_result()
        assert isinstance(output, VNAResult)

    @pytest.mark.parametrize("command, arg", [(":SENS1:AVER:CLE", ""), ("SENS1:AVER:COUN", "3")])
    def test_send_command_method(self, command, arg, e5071b: E5071B):
        """Test the send command method"""
        assert isinstance(command, str)
        assert isinstance(arg, str)
        e5071b.send_command(command, arg)
        e5071b.device.send_command.assert_called_with(f"{command} {arg}")

    @pytest.mark.parametrize("continuous", [True, False])
    def test_continuous_method(self, continuous, e5071b: E5071B):
        """Test the continuous method"""
        e5071b.continuous(continuous)
        if continuous:
            e5071b.device.send_command.assert_called_with(":INIT:CONT ON ")
        else:
            e5071b.device.send_command.assert_called_with(":INIT:CONT OFF ")

    def test_set_timeout_method(self, e5071b: E5071B):
        """Test the set timeout method"""
        e5071b.set_timeout(100)
        e5071b.device.set_timeout.assert_called_with(100)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.POWER, -60.0),
            (Parameter.IF_BANDWIDTH, 50.0),
            (Parameter.ELECTRICAL_DELAY, 0.0),
        ],
    )
    def test_setup_properties(self, parameter: Parameter, value, e5071b: E5071B):
        assert isinstance(parameter, Parameter)
        e5071b.setup(parameter, value)
        if parameter == Parameter.POWER:
            assert e5071b.power == value
            e5071b.device.send_command.assert_called_with(f":SOUR1:POW:LEV:IMM:AMPL {value}")
        if parameter == Parameter.ELECTRICAL_DELAY:
            assert e5071b.electrical_delay == value
            e5071b.device.send_command.assert_called_with(f"CALC:MEAS:CORR:EDEL:TIME {value}")
        if parameter == Parameter.IF_BANDWIDTH:
            assert e5071b.if_bandwidth == value
            e5071b.device.send_command.assert_called_with(f":SENS1:BAND:RES {value}")

    def test_power_property(self, e5071b_no_device: E5071B):
        """Test power property"""
        assert hasattr(e5071b_no_device, "power")
        assert e5071b_no_device.power == e5071b_no_device.settings.power

    def test_electrical_delay_property(self, e5071b_no_device: E5071B):
        """Test the electrical delay property"""
        assert hasattr(e5071b_no_device, "electrical_delay")
        assert e5071b_no_device.electrical_delay == e5071b_no_device.settings.electrical_delay

    def test_if_bandwidth_property(self, e5071b_no_device: E5071B):
        """Test the if bandwidth property"""
        assert hasattr(e5071b_no_device, "if_bandwidth")
        assert e5071b_no_device.if_bandwidth == e5071b_no_device.settings.if_bandwidth
