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

    def test_qubit_ids_property(self, resonator: Resonator):
        """Test qubit_ids property."""
        assert resonator.qubit_ids == [qubit.id_ for qubit in resonator.qubits]

    def test_get_qubit_method(self, resonator: Resonator):
        """Test get_qubit property."""
        assert resonator.get_qubit(id_=resonator.qubits[0].id_) == resonator.qubits[0]
