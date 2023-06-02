import pytest

from qililab.chip import Chip, Port, Qubit, Resonator
from qililab.typings.enums import Line


@pytest.fixture(name="chip")
def fixture_chip():
    """Fixture that returns an instance of a ``Chip`` class."""
    settings = {
        "id_": 0,
        "category": "chip",
        "nodes": [
            {"name": "port", "id_": 0, "line": Line.FLUX.value, "nodes": [11]},
            {"name": "port", "id_": 1, "line": Line.DRIVE.value, "nodes": [11]},
            {"name": "port", "id_": 2, "line": Line.FEEDLINE_INPUT.value, "nodes": [10]},
            {"name": "port", "id_": 3, "line": Line.FEEDLINE_OUTPUT.value, "nodes": [10]},
            {"name": "resonator", "alias": "resonator", "id_": 10, "frequency": 8072600000, "nodes": [2, 3, 11]},
            {
                "name": "qubit",
                "alias": "qubit",
                "id_": 11,
                "qubit_index": 0,
                "frequency": 6532800000,
                "nodes": [0, 1, 10],
            },
        ],
    }
    return Chip(**settings)


class TestChip:
    """Unit tests for the ``Chip`` class."""

    def test_get_port_from_qubit_idx_method(self, chip: Chip):
        """Test ``get_port_from_qubit_idx`` method"""
        flux_port = chip.get_port_from_qubit_idx(idx=0, line=Line.FLUX)
        control_port = chip.get_port_from_qubit_idx(idx=0, line=Line.DRIVE)
        readout_port = chip.get_port_from_qubit_idx(idx=0, line=Line.FEEDLINE_INPUT)
        assert flux_port == 0
        assert control_port == 1
        assert readout_port == 2

    def test_get_port_from_qubit_idx_method_raises_error_when_no_port_found(self, chip: Chip):
        """Test ``get_port_from_qubit_idx`` method raises error when no port is found"""
        port_ids = set()
        for node in chip.nodes.copy():
            if isinstance(node, Port):
                port_ids.add(node.id_)
                chip.nodes.remove(node)
        for node in chip.nodes:
            if isinstance(node, (Qubit, Resonator)):
                for adj_node in node.nodes.copy():
                    if adj_node in port_ids:
                        node.nodes.remove(adj_node)

        for line in [Line.FLUX, Line.DRIVE, Line.FEEDLINE_INPUT, Line.FEEDLINE_OUTPUT]:
            with pytest.raises(ValueError, match=f"Qubit with index {0} doesn't have a {line} line."):
                chip.get_port_from_qubit_idx(idx=0, line=line)
