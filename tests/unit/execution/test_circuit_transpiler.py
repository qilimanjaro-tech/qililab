# pylint: disable=no-member

"""Tests for the Operation class."""
from typing import Tuple

import pytest
import rustworkx as rx

from qililab.circuit import Circuit
from qililab.circuit.nodes import EntryNode, Node, OperationNode
from qililab.circuit.operations import R180, Barrier, Measure, Operation, Reset, Rxy, Wait, X
from qililab.circuit.operations.translatable_to_pulse_operations.cphase import CPhase
from qililab.execution.circuit_transpiler import CircuitTranspiler
from qililab.platform import Platform
from qililab.settings.runcard_schema import RuncardSchema
from qililab.typings.enums import OperationMultiplicity, OperationTimingsCalculationMethod


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


@pytest.fixture(name="empty_circuit")
def fixture_empty_circuit() -> Circuit:
    """Return a circuit with no operations."""
    circuit = Circuit(2)
    return circuit


class TestCircuitTranspiler:
    """Unit tests checking the CircuitTranspiler attributes and methods"""

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    def test_properties_after_init(self, request: pytest.FixtureRequest, circuit_fixture: str, platform: Platform):
        circuit = request.getfixturevalue(circuit_fixture)
        transpiler = CircuitTranspiler(circuit=circuit, settings=platform.settings)
        assert isinstance(transpiler.circuit, Circuit)
        assert isinstance(transpiler.settings, RuncardSchema.PlatformSettings)
        assert transpiler.circuit_ir1 is None
        assert transpiler.circuit_ir2 is None

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    @pytest.mark.parametrize(
        "timings_calculation_method",
        [OperationTimingsCalculationMethod.AS_SOON_AS_POSSIBLE, OperationTimingsCalculationMethod.AS_LATE_AS_POSSIBLE],
    )
    def test_calculate_timings_method(
        self,
        request: pytest.FixtureRequest,
        circuit_fixture: str,
        timings_calculation_method: OperationTimingsCalculationMethod,
        platform: Platform,
    ):
        """Test num_qubits property"""
        circuit = request.getfixturevalue(circuit_fixture)
        settings = platform.settings
        settings.timings_calculation_method = timings_calculation_method
        transpiler = CircuitTranspiler(circuit, settings)
        circuit_ir1 = transpiler.calculate_timings()
        assert isinstance(circuit_ir1, Circuit)
        assert circuit_ir1.depth == circuit.depth

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    def test_translate_to_pulse_operations_method(
        self, request: pytest.FixtureRequest, circuit_fixture: str, platform: Platform
    ):
        """Test num_qubits property"""
        circuit = request.getfixturevalue(circuit_fixture)
        transpiler = CircuitTranspiler(circuit, platform.settings)
        circuit_ir2 = transpiler.translate_to_pulse_operations()
        assert isinstance(circuit_ir2, Circuit)
        assert circuit_ir2.depth == circuit.depth
