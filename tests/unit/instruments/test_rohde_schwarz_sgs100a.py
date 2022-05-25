"""Tests for the SGS100A class."""
import pytest

from qililab.instruments import SGS100A


class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    def test_connect_method_raises_error(self, rohde_schwarz: SGS100A):
        """Test that calling again connect raises a ValueError"""
        with pytest.raises(ValueError):
            rohde_schwarz.connect()

    def test_start_method(self, rohde_schwarz: SGS100A):
        """Test start method"""
        rohde_schwarz.start()
        rohde_schwarz.device.on.assert_called_once()  # type: ignore

    def test_setup_method(self, rohde_schwarz: SGS100A):
        """Test setup method"""
        rohde_schwarz.setup()
        rohde_schwarz.device.power.assert_called_once_with(rohde_schwarz.power)
        rohde_schwarz.device.frequency.assert_called_once_with(rohde_schwarz.frequency)

    def test_stop_method(self, rohde_schwarz: SGS100A):
        """Test stop method"""
        rohde_schwarz.stop()
        rohde_schwarz.device.off.assert_called_once()  # type: ignore

    def test_close_method(self, rohde_schwarz: SGS100A):
        """Test close method"""
        rohde_schwarz.close()
        rohde_schwarz.device.off.assert_called_once()  # type: ignore
        rohde_schwarz.device.close.assert_called_once()  # type: ignore

    def test_not_connected_attribute_error(self, rohde_schwarz: SGS100A):
        """Test that calling a method when the device is not connected raises an AttributeError."""
        rohde_schwarz.close()
        with pytest.raises(AttributeError):
            rohde_schwarz.start()
