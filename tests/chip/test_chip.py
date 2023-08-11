import pytest

from qililab.chip import Chip, Port, Qubit, Resonator
from qililab.typings.enums import Line


@pytest.fixture(name="chip")
def fixture_chip():
    """Fixture that returns an instance of a ``Chip`` class."""
    settings = {
        "nodes": [
            {"name": "port", "alias": "flux_q0", "line": Line.FLUX.value, "nodes": ["q0"]},
            {"name": "port", "alias": "drive_q0", "line": Line.DRIVE.value, "nodes": ["q0"]},
            {"name": "port", "alias": "feedline_input", "line": Line.FEEDLINE_INPUT.value, "nodes": ["resonator"]},
            {"name": "port", "alias": "feedline_output", "line": Line.FEEDLINE_OUTPUT.value, "nodes": ["resonator"]},
            {
                "name": "resonator",
                "alias": "resonator",
                "frequency": 8072600000,
                "nodes": ["feedline_input", "feedline_output", "q0"],
            },
            {
                "name": "qubit",
                "alias": "q0",
                "qubit_index": 0,
                "frequency": 6532800000,
                "nodes": ["flux_q0", "drive_q0", "resonator"],
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
        assert flux_port == "flux_q0"
        assert control_port == "drive_q0"
        assert readout_port == "feedline_input"

    def test_get_port_from_qubit_idx_method_raises_error_when_no_port_found(self, chip: Chip):
        """Test ``get_port_from_qubit_idx`` method raises error when no port is found"""
        port_aliases = set()
        for node in chip.nodes.copy():
            if isinstance(node, Port):
                port_aliases.add(node.alias)
                chip.nodes.remove(node)
        for node in chip.nodes:
            if isinstance(node, (Qubit, Resonator)):
                for adj_node in node.nodes.copy():
                    if adj_node in port_aliases:
                        node.nodes.remove(adj_node)

        for line in [Line.FLUX, Line.DRIVE, Line.FEEDLINE_INPUT, Line.FEEDLINE_OUTPUT]:
            with pytest.raises(ValueError, match=f"Qubit with index {0} doesn't have a {line} line."):
                chip.get_port_from_qubit_idx(idx=0, line=line)

    def test_print_chip(self, chip: Chip):
        """Test print chip."""
        gotten_string = f"Chip with {chip.num_qubits} qubits and {chip.num_ports} ports: \n\n"
        for node in chip.nodes:
            if isinstance(node, Port):
                adj_nodes = chip._get_adjacent_nodes(node=node)
                gotten_string += f" * Port {node.alias} ({node.line.value}): ----"
                for adj_node in adj_nodes:
                    gotten_string += f"|{adj_node}|--"
                gotten_string += "--\n"

        assert str(chip) == gotten_string
