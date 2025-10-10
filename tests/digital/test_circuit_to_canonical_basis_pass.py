import math

import pytest

from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CNOT,
    CZ,
    H,
    I,
    M,
    RX,
    RY,
    RZ,
    U3,
    Controlled,
    X,
    Y,
    Z,
)

from qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass import (
    CircuitToCanonicalBasisPass,
)


def gate_summary(circuit: Circuit) -> list[tuple[str, tuple[int, ...]]]:
    return [(type(g).__name__, g.qubits) for g in circuit.gates]


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
        circuit.add(I(0))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 4  # Identity removed

        g0, g1, g2, g3 = out.gates

        assert isinstance(g0, U3)
        assert g0.qubits == (0,)
        assert g0.theta == pytest.approx(math.pi / 2.0)
        assert g0.phi == pytest.approx(0.0)
        assert g0.gamma == pytest.approx(math.pi)

        assert isinstance(g1, RX)
        assert g1.qubits == (0,)
        assert g1.theta == pytest.approx(math.pi)

        assert isinstance(g2, RY)
        assert g2.qubits == (0,)
        assert g2.theta == pytest.approx(math.pi)

        assert isinstance(g3, RZ)
        assert g3.qubits == (0,)
        assert g3.phi == pytest.approx(math.pi)

    def test_converts_cnot_to_cz_sequence(self) -> None:
        circuit = Circuit(2)
        circuit.add(CNOT(0, 1))

        out = CircuitToCanonicalBasisPass().run(circuit)

        assert len(out.gates) == 3

        g0, g1, g2 = out.gates
        assert isinstance(g0, U3)
        assert g0.qubits == (1,)
        assert g0.theta == pytest.approx(math.pi / 2.0)
        assert g0.phi == pytest.approx(0.0)
        assert g0.gamma == pytest.approx(math.pi)

        assert isinstance(g1, CZ)
        assert g1.control_qubits == (0,)
        assert g1.target_qubits == (1,)

        assert isinstance(g2, U3)
        assert g2.qubits == (1,)
        assert g2.theta == pytest.approx(math.pi / 2.0)
        assert g2.phi == pytest.approx(0.0)
        assert g2.gamma == pytest.approx(math.pi)

    def test_expands_controlled_single_qubit_gate(self) -> None:
        circuit = Circuit(2)
        circuit.add(Controlled(1, basic_gate=RY(0, theta=0.3)))

        out = CircuitToCanonicalBasisPass().run(circuit)

        for gate in out.gates:
            assert isinstance(gate, (U3, RX, RY, RZ, CZ))

        # Ensure the generic Controlled gate vanished from the output
        assert all(type(gate) is not Controlled for gate in out.gates)
