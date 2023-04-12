"""Test for the VectorNetworkAnalyzer E5080B class."""
from unittest.mock import patch

import pytest

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.result.vna_result import VNAResult
from qililab.typings.enums import Parameter, VNAScatteringParameters, VNASweepModes, VNATriggerModes


class TestE5080B:
    """Unit tests checking the VectorNetworkAnalyzer E5080B attributes and methods"""

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.TRIGGER_MODE, "INT"),
            (Parameter.SCATTERING_PARAMETER, "S21"),
            (Parameter.SWEEP_MODE, "cont"),
            (Parameter.SWEEP_MODE, "hold"),
        ],
    )
    def test_setup_method_value_str(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method with str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        e5080b.setup(parameter, value)
        if parameter == Parameter.TRIGGER_MODE:
            assert e5080b.trigger_mode == VNATriggerModes(value)
        if parameter == Parameter.SCATTERING_PARAMETER:
            assert e5080b.scattering_parameter == VNAScatteringParameters(value)
        if parameter == Parameter.SWEEP_MODE:
            assert e5080b.sweep_mode == VNASweepModes(value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.SCATTERING_PARAMETER, "S221"),
            (Parameter.SCATTERING_PARAMETER, "s11"),
            (Parameter.SWEEP_MODE, "CONT"),
            (Parameter.SWEEP_MODE, "sweep_mode continuous"),
        ],
    )
    def test_setup_method_value_str_raises_exception(self, parameter: Parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect str value"""
        assert isinstance(parameter, Parameter)
        assert isinstance(value, str)
        with pytest.raises(ValueError):
            e5080b.setup(parameter, value)

    @pytest.mark.parametrize(
        "parameter, value",
        [
            (Parameter.CURRENT, "foo"),
            (Parameter.VOLTAGE, "bar"),
        ],
    )
    def test_setup_method_str_raises_exception(self, parameter, value, e5080b: E5080B):
        """Test the setup method raises exception with incorrect str parameter"""
        with pytest.raises(ParameterNotFound):
            e5080b.setup(parameter, value)

    def test_get_sweep_mode_method(self, e5080b: E5080B):
        """Test the get sweep mode method"""
        output = e5080b._get_sweep_mode()
        e5080b.device.send_query.assert_called()
        assert isinstance(output, str)

    def test_get_trace_method(self, e5080b: E5080B):
        """Test auxiliarty private method get trace."""
        e5080b._get_trace()
        e5080b.device.send_command.assert_called()
        e5080b.device.send_binary_query.assert_called_once()

    @pytest.mark.parametrize("count", ["1", "3", "5"])
    def test_set_count_method(self, count: str, e5080b: E5080B):
        """Test the auxiliary private method set count"""
        e5080b._set_count(count)
        e5080b.device.send_command.assert_called_with(command="SENS1:SWE:GRO:COUN", arg=count)

    def test_pre_measurement_method(self, e5080b: E5080B):
        """Test the auxiliary private method pre measurment"""
        e5080b._pre_measurement()
        assert e5080b.averaging_enabled

    def test_start_measurement_method(self, e5080b: E5080B):
        """Test the auxiliary private method start measurment"""
        e5080b._start_measurement()
        assert e5080b.sweep_mode == VNASweepModes("group")

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    def test_wait_until_ready_method(self, mock_ready, e5080b: E5080B):
        """Test the auxiliary private method wait until ready"""
        mock_ready.return_value = True
        output = e5080b._wait_until_ready()
        assert output

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    @patch.object(E5080B, "device_timeout", new=10)
    def test_wait_until_ready_method_fails(self, mock_ready, e5080b: E5080B):
        """Test the auxiliary private method wait until ready fails"""
        mock_ready.return_value = False
        output = e5080b._wait_until_ready()
        assert not output

    def test_average_clear_method(self, e5080b: E5080B):
        """Test the average clear method"""
        e5080b.average_clear()
        e5080b.device.send_command.assert_called()

    def test_get_frequencies_method(self, e5080b: E5080B):
        """Test the get frequencies method"""
        e5080b.get_frequencies()
        e5080b.device.send_binary_query.assert_called()

    def test_ready_method(self, e5080b: E5080B):
        """Test ready method"""
        output = e5080b.ready()
        assert isinstance(output, bool)

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B._get_sweep_mode")
    def test_ready_method_raises_exception(self, mock_get_sweep_mode, e5080b: E5080B):
        """Test read method raises an Exception"""
        mock_get_sweep_mode.side_effect = ValueError("Mocked exception")
        output = e5080b.ready()
        assert not output
        with pytest.raises(Exception) as exc:
            e5080b.ready()
            assert exc == Exception

    def test_release_method(self, e5080b: E5080B):
        """Test release method"""
        e5080b.release()
        assert e5080b.settings.sweep_mode == VNASweepModes("cont")

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    def test_read_tracedata_method(self, mock_ready, e5080b: E5080B):
        """Test the read tracedata method"""
        mock_ready.return_value = True
        output = e5080b.read_tracedata()
        assert output is not None

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    @patch.object(E5080B, "device_timeout", new=10)
    def test_read_tracedata_method_raises_exception(self, mock_ready, e5080b: E5080B):
        """Test the read tracedata method"""
        mock_ready.return_value = False
        with pytest.raises(TimeoutError):
            e5080b.read_tracedata()

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    def test_acquire_result_method(self, mock_ready, e5080b: E5080B):
        """Test the acquire result method"""
        mock_ready.return_value = True
        output = e5080b.acquire_result()
        assert isinstance(output, VNAResult)

    def test_sweep_mode_property(self, e5080b: E5080B):
        """Test the sweep mode property"""
        assert hasattr(e5080b, "sweep_mode")
        assert e5080b.sweep_mode == e5080b.settings.sweep_mode

    @pytest.mark.parametrize("value", ["foo", "bar"])
    def test_sweep_mode_property_fails(self, value, e5080b: E5080B):
        """Test the sweep mode property setter raises an exception"""
        with pytest.raises(ValueError):
            e5080b.sweep_mode = value
