# pylint: disable=no-member

"""Tests for the Operation class."""
import io
import os
from contextlib import redirect_stdout
from typing import Tuple
from unittest.mock import patch

import pytest
import rustworkx as rx

from qililab.circuit import Circuit
from qililab.circuit.nodes import EntryNode
from qililab.circuit.operations import CPhase, DRAGPulse, GaussianPulse, Measure, Operation, Reset, SquarePulse, Wait, X
from qililab.typings.enums import OperationMultiplicity, OperationTimingsCalculationMethod


@pytest.fixture(name="parallel_circuit")
def fixture_parallel_circuit() -> Circuit:
    """Return a circuit with parallel operations only"""
    circuit = Circuit(2)
    circuit.add(0, SquarePulse(amplitude=1.0, duration=40, resolution=1.0))
    circuit.add(0, GaussianPulse(amplitude=1.0, duration=40, sigma=1.0))
    circuit.add(1, DRAGPulse(amplitude=1.0, duration=40, sigma=1.0, delta=2.0))
    return circuit


@pytest.fixture(name="parallel_circuit_print_output_soon")
def fixture_parallel_circuit_print_ouput_soon() -> str:
    """Return the print output of parallel circuit."""
    return "0:----Square--Gaussian\n" "1:------DRAG----------\n"


@pytest.fixture(name="parallel_circuit_print_output_late")
def fixture_parallel_circuit_print_ouput_late() -> str:
    """Return the print output of parallel circuit."""
    return "0:----Square--Gaussian\n" "1:----------------DRAG\n"


@pytest.fixture(name="simple_circuit")
def fixture_simple_circuit() -> Circuit:
    """Return a simple circuit."""
    circuit = Circuit(2)
    circuit.add(0, X())
    circuit.add(0, Wait(t=100))
    circuit.add(0, X())
    circuit.add(1, X())
    circuit.add((0, 1), Measure())
    return circuit


@pytest.fixture(name="simple_circuit_print_output_soon")
def fixture_simple_circuit_print_output_soon() -> str:
    """Return the print output of simple circuit."""
    return "0:---------X------Wait---------X---Measure\n" "1:---------X-----------------------Measure\n"


@pytest.fixture(name="simple_circuit_print_output_late")
def fixture_simple_circuit_print_output_late() -> str:
    """Return the print output of simple circuit."""
    return "0:---------X------Wait---------X---Measure\n" "1:-----------------------------X---Measure\n"


@pytest.fixture(name="empty_circuit")
def fixture_empty_circuit() -> Circuit:
    """Return a circuit with no operations."""
    circuit = Circuit(2)
    return circuit


@pytest.fixture(name="empty_circuit_print_output")
def fixture_empty_circuit_print_output() -> str:
    """Return the print output of simple circuit."""
    return "0:\n" "1:\n"


class TestCircuit:
    """Unit tests checking the Circuit attributes and methods"""

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    def test_init(self, request: pytest.FixtureRequest, circuit_fixture: str):
        """Test init method"""
        circuit = request.getfixturevalue(circuit_fixture)
        assert isinstance(circuit.num_qubits, int)
        assert isinstance(circuit.graph, rx.PyDiGraph)
        assert circuit.graph.multigraph is True
        assert isinstance(circuit.entry_node, EntryNode)
        assert isinstance(circuit.entry_node.index, int)

    @pytest.mark.parametrize("num_qubits", [-10, -1, 0])
    def test_init_raises_error_when_num_qubits_is_not_positive(self, num_qubits: int):
        """Test init method raises error when num_qubits parameter is not positive"""
        with pytest.raises(ValueError, match="Number of qubits should be positive."):
            Circuit(num_qubits=num_qubits)

    @pytest.mark.parametrize("num_qubits", [1.0, 5.2, 10e9])
    def test_init_raises_error_when_num_qubits_is_not_integer(self, num_qubits: int):
        """Test init method raises error when num_qubits parameter is not an integer"""
        with pytest.raises(ValueError, match="Number of qubits should be integer."):
            Circuit(num_qubits=num_qubits)

    @pytest.mark.parametrize(
        "circuit_fixture,expected_depth",
        [("simple_circuit", 4), ("empty_circuit", 0)],
    )
    def test_depth_parameter(self, request: pytest.FixtureRequest, circuit_fixture: str, expected_depth: int):
        """Test that depth parameter returns correct value"""
        circuit = request.getfixturevalue(circuit_fixture)
        depth = circuit.depth
        assert isinstance(depth, int)
        assert depth == expected_depth

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    @pytest.mark.parametrize(
        "qubits,operation",
        [(0, X()), (1, X()), (0, Reset()), ((0, 1), Reset()), ((0, 1), Measure()), ((0, 1), CPhase(theta=90))],
    )
    def test_add_method_should_add_correct_nodes(
        self, request: pytest.FixtureRequest, circuit_fixture: str, qubits: int | Tuple[int, ...], operation: Operation
    ):
        """Test that add method adds correct number of nodes"""
        circuit = request.getfixturevalue(circuit_fixture)
        number_of_nodes_before = circuit.graph.num_nodes()
        num_qubits = len(qubits) if isinstance(qubits, tuple) else 1
        number_of_nodes_that_should_be_added = (
            num_qubits if operation.multiplicity == OperationMultiplicity.PARALLEL else 1
        )
        circuit.add(qubits=qubits, operation=operation)
        number_of_nodes_after = circuit.graph.num_nodes()
        assert number_of_nodes_after == number_of_nodes_before + number_of_nodes_that_should_be_added

    @pytest.mark.parametrize(
        "circuit_fixture,timings_method,expected_output_fixture",
        [
            (
                "simple_circuit",
                OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE,
                "simple_circuit_print_output_soon",
            ),
            (
                "simple_circuit",
                OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE,
                "simple_circuit_print_output_late",
            ),
            (
                "parallel_circuit",
                OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE,
                "parallel_circuit_print_output_soon",
            ),
            (
                "parallel_circuit",
                OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE,
                "parallel_circuit_print_output_late",
            ),
            ("empty_circuit", OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE, "empty_circuit_print_output"),
            ("empty_circuit", OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE, "empty_circuit_print_output"),
        ],
    )
    def test_print_method(
        self,
        request: pytest.FixtureRequest,
        circuit_fixture: str,
        timings_method: OperationTimingsCalculationMethod,
        expected_output_fixture: str,
    ):
        """Test print method"""
        circuit = request.getfixturevalue(circuit_fixture)
        expected_output = request.getfixturevalue(expected_output_fixture)

        # Capture the printed output using io.StringIO
        with io.StringIO() as buf, redirect_stdout(buf):
            circuit.print(method=timings_method)
            printed_output = buf.getvalue()

        assert printed_output == expected_output

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    def test_draw_save_to_file(self, tmpdir, request: pytest.FixtureRequest, circuit_fixture: str):
        """Test that draw method is saving to file when filename is provided"""
        circuit = request.getfixturevalue(circuit_fixture)
        output_file = str(tmpdir.join(f"{circuit_fixture}.png"))
        circuit.draw(filename=output_file)
        assert os.path.exists(output_file), f"Output file {output_file} does not exist."
        os.remove(output_file)

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    def test_draw_display_image(self, monkeypatch, request: pytest.FixtureRequest, circuit_fixture: str):
        """Test that draw method is displaying the image when filename is not provided"""
        circuit = request.getfixturevalue(circuit_fixture)
        with patch("PIL.Image.Image.show") as mock_show:
            circuit.draw()
            mock_show.assert_called_once()
