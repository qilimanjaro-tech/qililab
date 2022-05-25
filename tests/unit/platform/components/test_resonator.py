"""Tests for the Resonator class."""
from qililab.platform import Resonator
from qililab.typings import BusElementName


class Testresonator:
    """Unit tests checking the Resonator attributes and methods."""

    def test_id_property(self, resonator: Resonator):
        """Test id property."""
        assert resonator.id_ == resonator.settings.id_

    def test_name_property(self, resonator: Resonator):
        """Test name property."""
        assert resonator.name == BusElementName.RESONATOR

    def test_category_property(self, resonator: Resonator):
        """Test name property."""
        assert resonator.category == resonator.settings.category

    def test_qubits_property(self, resonator: Resonator):
        """Test qubits property."""
        assert resonator.qubits == resonator.settings.qubits
