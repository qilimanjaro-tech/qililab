"""Test for the VectorNetworkAnalyzer class."""
import copy
from unittest.mock import MagicMock, patch

import pytest
import pyvisa

from qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller import E5080BController
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.platform import Platform
from qililab.result.vna_result import VNAResult
from tests.data import SauronVNA


@pytest.fixture(name="vector_network_analyzer_controller")
def fixture_e5080b_controller(sauron_platform: Platform):
    """Return an instance of VectorNetworkAnalyzer controller class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b_controller)
    settings.pop("name")
    return E5080BController(settings=settings, loaded_instruments=sauron_platform.instruments)


@pytest.fixture(name="vector_network_analyzer_no_device")
def fixture_e5080b_no_device():
    """Return an instance of VectorNetworkAnalyzer class"""
    settings = copy.deepcopy(SauronVNA.keysight_e5080b)
    settings.pop("name")
    return E5080B(settings=settings)


@pytest.fixture(name="vector_network_analyzer")
@patch(
    "qililab.instrument_controllers.vector_network_analyzer.keysight_E5080B_vna_controller.E5080BDriver",
    autospec=True,
)
def fixture_e5080b(mock_device: MagicMock, vector_network_analyzer_controller: E5080BController):
    """Return connected instance of VectorNetworkAnalyzer class"""
    mock_instance = mock_device.return_value
    mock_instance.mock_add_spec(["power"])
    vector_network_analyzer_controller.connect()
    mock_device.assert_called()
    return vector_network_analyzer_controller.modules[0]


class TestVectorNetworkAnalyzer:
    """Unit tests checking the VectorNetworkAnalyzer methods"""

    def test_to_dict_method(self, vector_network_analyzer_no_device: E5080B):
        """Test the dict method"""
        assert isinstance(vector_network_analyzer_no_device.to_dict(), dict)

    def test_initial_setup_method(self, vector_network_analyzer: E5080B):
        """Test the initial setup method"""
        vector_network_analyzer.initial_setup()
        vector_network_analyzer.device.initial_setup.assert_called()

    def test_reset_method(self, vector_network_analyzer: E5080B):
        """Test the reset method"""
        vector_network_analyzer.reset()
        vector_network_analyzer.device.reset.assert_called()

    def test_turn_on_method(self, vector_network_analyzer: E5080B):
        """Test turn on method"""
        vector_network_analyzer.turn_on()
        vector_network_analyzer.device.send_command.assert_called_with(command=":OUTP", arg="ON")

    def test_turn_off_method(self, vector_network_analyzer: E5080B):
        """Test turn off method"""
        vector_network_analyzer.turn_off()
        vector_network_analyzer.device.send_command.assert_called_with(command=":OUTP", arg="OFF")

    @pytest.mark.parametrize("command", [":SENS1:AVER:CLE", "SENS1:AVER:COUN 3"])
    def test_send_command_method(self, command: str, vector_network_analyzer: E5080B):
        """Test the send command method"""
        assert isinstance(command, str)
        vector_network_analyzer.send_command(command)
        vector_network_analyzer.device.send_command.assert_called_with(command=command, arg="")

    @pytest.mark.parametrize("query", [":SENS1:SWE:MODE?"])
    def test_send_query_method(self, query: str, vector_network_analyzer: E5080B):
        """Test the send query method"""
        assert isinstance(query, str)
        vector_network_analyzer.send_query(query)
        vector_network_analyzer.device.send_query.assert_called_with(query)

    @pytest.mark.parametrize("query", ["SENS:X?", "CALC1:MEAS1:DATA:SDAT?"])
    def test_send_binary_query_method(self, query: str, vector_network_analyzer: E5080B):
        """Test the send binary query method"""
        assert isinstance(query, str)
        vector_network_analyzer.send_binary_query(query)
        vector_network_analyzer.device.send_binary_query.assert_called_with(query)

    @patch("qililab.instruments.keysight.e5080b_vna.E5080B.ready")
    def test_acquire_result_method(self, mock_ready, vector_network_analyzer: E5080B):
        """Test the acquire result method"""
        mock_ready.return_value = True
        output = vector_network_analyzer.acquire_result()
        assert isinstance(output, VNAResult)


class TestVectorNetworkAnalyzerDriver:
    """Test for the driver class at typings"""

    def test_post_init_method(self, vector_network_analyzer: E5080B):
        """Test the postinit function from the driver"""
        vector_network_analyzer.device.__post_init__()
        vector_network_analyzer.device.pyvisa.ResourceManager.assert_called_with("@py")
        assert isinstance(vector_network_analyzer.device.driver, pyvisa.Resource)

    def test_initial_setup_method(self, vector_network_analyzer: E5080B):
        """Test the initial setup method of the driver"""
        vector_network_analyzer.device.initial_setup()
        vector_network_analyzer.device.driver.write.assert_called_with("FORM:DATA REAL,32")
        vector_network_analyzer.device.driver.write.assert_called_with("*CLS")
        vector_network_analyzer.device.driver.write.assert_called_with("SYST:PRES; *OPC?")

    def test_reset_method(self, vector_network_analyzer: E5080B):
        """Test the reset method of the driver"""
        vector_network_analyzer.device.initial_setup()
        vector_network_analyzer.device.driver.write.assert_called_with("SYST:PRES; *OPC?")

    def test_send_command(self, command, arg, vector_network_analyzer: E5080B):
        """Test the send command method of the driver"""
        vector_network_analyzer.device.send_command(command, arg)
        vector_network_analyzer.device.driver.write.assert_called_with(f"{command} {arg}")

    def test_send_query_method(self, query, vector_network_analyzer: E5080B):
        """Test the send query method of the driver"""
        vector_network_analyzer.device.send_query(query)
        vector_network_analyzer.device.driver.query.assert_called_with(query)

    def test_send_binary_query_method(self, query, vector_network_analyzer: E5080B):
        """Test the send binary query method of the driver"""
        vector_network_analyzer.device.send_binary_query(query)
        vector_network_analyzer.device.driver.query_binary_values.assert_called_with(query)

    def test_set_timeput_method(self, value, vector_network_analyzer: E5080B):
        """Test the set timeout method of the driver"""
        vector_network_analyzer.device.set_timeout(value)
        assert vector_network_analyzer.device.timeout == value
