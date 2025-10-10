import math
from typing import Any

import numpy as np
import pytest

from qilisdk.digital import Circuit
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qilisdk.digital.gates import (
    Adjoint,
    CNOT,
    CZ,
    Exponential,
    H,
    I,
    M,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    BasicGate,
    Controlled,
    Gate,
    X,
    Y,
    Z,
)

from qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass import (
    CircuitToCanonicalBasisPass,
)


def gate_summary(circuit: Circuit) -> list[tuple[str, tuple[int, ...]]]:
    return [(type(g).__name__, g.qubits) for g in circuit.gates]


class Custom1QGate(BasicGate):
    def __init__(self, qubit: int, matrix: np.ndarray) -> None:
        self._matrix_override = matrix
        super().__init__((qubit,), {})

    @property
    def name(self) -> str:
        return "Custom1QGate"

    def _generate_matrix(self) -> np.ndarray:
        return self._matrix_override


class Custom2QGate(BasicGate):
    def __init__(self, qubits: tuple[int, int], matrix: np.ndarray) -> None:
        self._matrix_override = matrix
        super().__init__(qubits, {})

    @property
    def name(self) -> str:
        return "Custom2QGate"

    def _generate_matrix(self) -> np.ndarray:
        return self._matrix_override


class TestCircuitToCanonicalBasisPass:
    def test_preserves_basis_gates(self) -> None:
        circuit = Circuit(2)
        circuit.add(U3(0, theta=0.1, phi=0.2, gamma=0.3))
        circuit.add(RX(0, theta=-0.4))
        circuit.add(RY(1, theta=0.5))
        circuit.add(RZ(1, phi=-0.6))
        circuit.add(CZ(0, 1))
        circuit.add(M(0))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert gate_summary(out) == gate_summary(circuit)
        assert len(out.gates) == len(circuit.gates)

    def test_rewrites_standard_generators(self) -> None:
        circuit = Circuit(1)
        circuit.add(H(0))
        circuit.add(X(0))
        circuit.add(Y(0))
        circuit.add(Z(0))
        circuit.add(I(0))  # should vanish

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 4
        names = [type(g).__name__ for g in out.gates]
        assert names == ["U3", "RX", "RY", "RZ"]
        assert all(g.qubits == (0,) for g in out.gates)

    def test_parametric_1q_conversions(self) -> None:
        circuit = Circuit(1)
        circuit.add(U1(0, phi=0.7))
        circuit.add(U2(0, phi=0.1, gamma=0.2))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 2
        assert isinstance(out.gates[0], RZ)
        assert out.gates[0].phi == pytest.approx(0.7)
        assert isinstance(out.gates[1], U3)
        assert out.gates[1].theta == pytest.approx(math.pi / 2.0)
        assert out.gates[1].phi == pytest.approx(0.1)
        assert out.gates[1].gamma == pytest.approx(0.2)

    def test_converts_cnot_to_cz_sequence(self) -> None:
        circuit = Circuit(2)
        circuit.add(CNOT(0, 1))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 3
        assert isinstance(out.gates[0], U3)
        assert isinstance(out.gates[1], CZ)
        assert isinstance(out.gates[2], U3)

    def test_expands_swap(self) -> None:
        circuit = Circuit(2)
        circuit.add(SWAP(0, 1))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 9
        assert all(isinstance(g, (U3, RZ, RX, RY, CZ)) for g in out.gates)

    def test_expands_controlled_single_qubit_gate(self) -> None:
        circuit = Circuit(2)
        circuit.add(Controlled(1, basic_gate=RY(0, theta=0.3)))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert all(isinstance(g, (U3, RX, RY, RZ, CZ)) for g in out.gates)
        assert all(type(g) is not Controlled for g in out.gates)

    def test_multi_controlled_gate(self) -> None:
        circuit = Circuit(3)
        circuit.add(Controlled(1, 2, basic_gate=RX(0, theta=0.4)))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert all(isinstance(g, (U3, RX, RY, RZ, CZ)) for g in out.gates)
        assert all(type(g) is not Controlled for g in out.gates)

    def test_adjoint_gate(self) -> None:
        circuit = Circuit(1)
        circuit.add(Adjoint(H(0)))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 1
        gate = out.gates[0]
        assert isinstance(gate, U3)
        assert gate.theta == pytest.approx(-math.pi / 2.0)

    def test_exponential_of_single_qubit_gate(self) -> None:
        circuit = Circuit(1)
        circuit.add(Exponential(RY(0, theta=0.2)))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 1
        assert isinstance(out.gates[0], U3)

    def test_generic_basic_gate_fallback(self) -> None:
        matrix = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex)  # behaves like X
        circuit = Circuit(1)
        circuit.add(Custom1QGate(0, matrix))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 1
        assert isinstance(out.gates[0], U3)

    def test_not_implemented_for_multi_qubit_exponential(self) -> None:
        matrix = np.eye(4, dtype=complex)
        circuit = Circuit(2)
        circuit.add(Custom2QGate((0, 1), matrix).exponential())

        with pytest.raises(NotImplementedError):
            CircuitToCanonicalBasisPass().run(circuit)

    def test_measurements_pass_through(self) -> None:
        circuit = Circuit(1)
        circuit.add(M(0))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert gate_summary(out) == [("M", (0,))]
