"""Tests for the SGS100A class."""

from qililab.instruments import SGS100A


class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    def test_start_method(self, rohde_schwarz: SGS100A):
        """Test start method"""
        rohde_schwarz.start()
        rohde_schwarz.device.on.assert_called_once()  # type: ignore

    def test_setup_method(self, rohde_schwarz: SGS100A):
        """Test setup method"""
        rohde_schwarz.setup()
        rohde_schwarz.device.power.assert_called_once_with(rohde_schwarz.power)

    def test_stop_method(self, rohde_schwarz: SGS100A):
        """Test stop method"""
        rohde_schwarz.stop()
        rohde_schwarz.device.off.assert_called_once()  # type: ignore
