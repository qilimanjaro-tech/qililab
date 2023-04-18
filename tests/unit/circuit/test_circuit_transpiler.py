# pylint: disable=no-member

"""Tests for the Operation class."""
from dataclasses import dataclass

import pytest

from qililab.circuit import Circuit
from qililab.circuit.circuit_transpiler import CircuitTranspiler
from qililab.circuit.operations import Barrier, Measure, Reset, SquarePulse, Wait, X
from qililab.circuit.operations.operation import Operation
from qililab.platform import Platform
from qililab.settings.runcard_schema import RuncardSchema
from qililab.typings.enums import OperationMultiplicity, OperationName, OperationTimingsCalculationMethod
from qililab.utils import classproperty


@pytest.fixture(name="simple_circuit")
def fixture_simple_circuit() -> Circuit:
    """Return a simple circuit."""
    circuit = Circuit(2)
    circuit.add(0, X())
    circuit.add(0, Wait(t=100))
    circuit.add(1, SquarePulse(amplitude=1.0, duration=40, resolution=1.0))
    circuit.add((0, 1), Barrier())
    circuit.add(0, X())
    circuit.add(1, X())
    circuit.add((0, 1), Measure())
    circuit.add((0, 1), Reset())
    return circuit


@pytest.fixture(name="empty_circuit")
def fixture_empty_circuit() -> Circuit:
    """Return a circuit with no operations."""
    circuit = Circuit(2)
    return circuit


class TestCircuitTranspiler:
    """Unit tests checking the CircuitTranspiler attributes and methods"""

    def test_properties_after_init(self, platform: Platform):
        transpiler = CircuitTranspiler(settings=platform.settings)
        assert isinstance(transpiler.settings, RuncardSchema.PlatformSettings)

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
        """Test calculate_timings method"""
        circuit = request.getfixturevalue(circuit_fixture)
        settings = platform.settings
        settings.timings_calculation_method = timings_calculation_method
        transpiler = CircuitTranspiler(settings=settings)
        transpiled_circuit = transpiler.calculate_timings(circuit=circuit)
        assert isinstance(transpiled_circuit, Circuit)
        assert transpiled_circuit.depth == circuit.depth
        assert transpiled_circuit.has_timings_calculated is True

    @pytest.mark.parametrize(
        "circuit_fixture",
        ["simple_circuit", "empty_circuit"],
    )
    def test_translate_to_pulse_operations_method(
        self, request: pytest.FixtureRequest, circuit_fixture: str, platform: Platform
    ):
        """Test translate_to_pulses method"""
        circuit = request.getfixturevalue(circuit_fixture)
        transpiler = CircuitTranspiler(settings=platform.settings)
        transpiled_circuit = transpiler.transpile_to_pulse_operations(circuit=circuit)
        assert isinstance(transpiled_circuit, Circuit)
        assert transpiled_circuit.depth == circuit.depth
        assert transpiled_circuit.has_transpiled_to_pulses is True

    def test_calculate_timings_method_raises_error_when_operation_not_supported(self, platform: Platform):
        """Test num_qubits property"""

        @dataclass
        class UnkownOperation(Operation):
            @classproperty
            def name(self) -> OperationName:
                return OperationName.X

            @classproperty
            def multiplicity(self) -> OperationMultiplicity:
                return OperationMultiplicity.PARALLEL

            @property
            def parameters(self):
                return {}

        circuit = Circuit(1)
        circuit.add(0, UnkownOperation())
        transpiler = CircuitTranspiler(settings=platform.settings)
        with pytest.raises(ValueError):
            transpiler.calculate_timings(circuit=circuit)
