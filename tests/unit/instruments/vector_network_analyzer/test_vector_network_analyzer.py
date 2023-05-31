"""Test for the VectorNetworkAnalyzer class."""
from unittest.mock import MagicMock, patch

from qililab.typings.instruments import E5080BDriver
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


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
        vna_driver.driver.write.assert_called_with("SYST:PRES; *OPC")

    @patch("qililab.typings.instruments.vector_network_analyzer.pyvisa.ResourceManager")
    def test_keysight_reset_method(self, mock_resource_manager):
        mock_resource = MagicMock(name="mock_resource")
        mock_resource_manager.return_value.open_resource.return_value = mock_resource
        vna_keysight_driver = E5080BDriver("foo", "bar")
        vna_keysight_driver.reset()
        vna_keysight_driver.driver.write.assert_called_with("SYST:PRES; *OPC")

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
