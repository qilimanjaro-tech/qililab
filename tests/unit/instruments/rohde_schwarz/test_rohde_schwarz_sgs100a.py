"""Tests for the SGS100A class."""

from qililab.instruments import SGS100A


class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    def test_setup_method(self, rohde_schwarz: SGS100A):
        """Test setup method"""
        rohde_schwarz.setup()
        rohde_schwarz.device.power.assert_called_with(rohde_schwarz.power)

    def test_initial_setup_method(self, rohde_schwarz: SGS100A):
        """Test initial setup method"""
        rohde_schwarz.initial_setup()
        rohde_schwarz.device.power.assert_called_with(rohde_schwarz.power)

    def test_turn_on_method(self, rohde_schwarz: SGS100A):
        """Test turn_on method"""
        rohde_schwarz.turn_on()
        rohde_schwarz.device.on.assert_called_once()  # type: ignore

    def test_turn_off_method(self, rohde_schwarz: SGS100A):
        """Test turn_off method"""
        rohde_schwarz.turn_off()
        rohde_schwarz.device.off.assert_called_once()  # type: ignore

    def test_reset_method(self, rohde_schwarz: SGS100A):
        """Test reset method"""
        rohde_schwarz.reset()
