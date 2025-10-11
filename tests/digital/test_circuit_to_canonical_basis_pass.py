import math
from collections import Counter
from typing import Iterable

import numpy as np
import pytest

from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CNOT,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Adjoint,
    BasicGate,
    Controlled,
    Exponential,
    H,
    I,
    M,
    X,
    Y,
    Z,
)

from qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass import (
    CircuitToCanonicalBasisPass,
    _adjoint_1q,
    _as_basis_1q,
    _invert_basis_gate,
    _multi_controlled,
    _single_controlled,
    _sqrt_1q_gate_as_basis,
)


class DummyBasicGate(BasicGate):
    def __init__(self, target_qubits: Iterable[int], matrix: np.ndarray) -> None:
        self._custom_matrix = np.array(matrix, dtype=complex)
        super().__init__(tuple(target_qubits))

    @property
    def name(self) -> str:
        return "Dummy"

    def _generate_matrix(self) -> np.ndarray:
        return self._custom_matrix


def _count_gate_names(seq: list) -> Counter:
    return Counter(g.name for g in seq)


def test_invert_basis_gate_handles_known_types():
    gates = [
        U3(0, theta=0.2, phi=0.1, gamma=-0.3),
        RX(0, theta=0.4),
        RY(0, theta=-0.5),
        RZ(0, phi=0.7),
        CZ(0, 1),
        M(0),
        H(0),
        X(0),
        Y(0),
        Z(0),
    ]
    inverted = [_invert_basis_gate(g) for g in gates]
    assert [seq[0].name for seq in inverted[:5]] == ["U3", "RX", "RY", "RZ", "CZ"]
    assert inverted[5][0].name == "M"
    assert [seq[0].name for seq in inverted[6:]] == ["U3", "RX", "RY", "RZ"]

    dummy = DummyBasicGate((0,), np.eye(2))
    assert isinstance(_invert_basis_gate(dummy)[0], Adjoint)


def test_as_basis_1q_handles_standard_and_basic():
    dummy_matrix = np.eye(2, dtype=complex)
    dummy_gate = DummyBasicGate((0,), dummy_matrix)
    rx_gate = RX(0, theta=0.3)
    assert _as_basis_1q(rx_gate) is rx_gate
    assert isinstance(_as_basis_1q(H(0)), U3)
    assert isinstance(_as_basis_1q(X(0)), RX)
    assert isinstance(_as_basis_1q(Y(0)), RY)
    assert isinstance(_as_basis_1q(Z(0)), RZ)
    assert isinstance(_as_basis_1q(U1(0, phi=0.1)), RZ)
    assert isinstance(_as_basis_1q(U2(0, phi=0.1, gamma=0.2)), U3)
    assert isinstance(_as_basis_1q(dummy_gate), U3)
    with pytest.raises(NotImplementedError):
        _as_basis_1q(Controlled(1, basic_gate=RX(0, theta=0.5)))


def test_sqrt_gate_as_basis_and_adjoint_variants():
    assert isinstance(_sqrt_1q_gate_as_basis(RZ(0, phi=math.pi)), RZ)
    assert isinstance(_sqrt_1q_gate_as_basis(RX(0, theta=math.pi)), RX)
    assert isinstance(_sqrt_1q_gate_as_basis(RY(0, theta=math.pi)), RY)
    assert isinstance(_sqrt_1q_gate_as_basis(Z(0)), RZ)
    assert isinstance(_sqrt_1q_gate_as_basis(X(0)), RX)
    assert isinstance(_sqrt_1q_gate_as_basis(Y(0)), RY)
    assert isinstance(_sqrt_1q_gate_as_basis(U1(0, phi=0.6)), RZ)
    assert isinstance(_sqrt_1q_gate_as_basis(U2(0, phi=0.1, gamma=0.2)), U3)
    assert isinstance(_sqrt_1q_gate_as_basis(U3(0, theta=0.2, phi=0.1, gamma=-0.4)), U3)
    dummy = DummyBasicGate((0,), np.eye(2))
    assert isinstance(_sqrt_1q_gate_as_basis(dummy), U3)
    assert isinstance(_sqrt_1q_gate_as_basis(H(0)), U3)

    assert isinstance(_adjoint_1q(RX(0, theta=0.5)), RX)
    assert isinstance(_adjoint_1q(RY(0, theta=0.5)), RY)
    assert isinstance(_adjoint_1q(RZ(0, phi=0.5)), RZ)
    assert isinstance(_adjoint_1q(U3(0, theta=0.5, phi=0.2, gamma=-0.1)), U3)
    assert isinstance(_adjoint_1q(H(0)), U3)


def test_sqrt_gate_recurses_for_wrapper(monkeypatch):
    from qilisdk.digital.gates import Gate as SDKGate

    class WrapperGate(SDKGate):
        def __init__(self, qubit: int) -> None:
            super().__init__()
            self._qubits = (qubit,)

        @property
        def name(self) -> str:
            return "Wrapper"

        @property
        def qubits(self) -> tuple[int, ...]:
            return self._qubits

        @property
        def target_qubits(self) -> tuple[int, ...]:
            return self._qubits

        @property
        def control_qubits(self) -> tuple[int, ...]:
            return ()

        @property
        def matrix(self) -> np.ndarray:
            return RX(self._qubits[0], theta=0.3).matrix

        @property
        def nqubits(self) -> int:
            return 1

    def patched_as_basis(gate):
        if isinstance(gate, WrapperGate):
            return RX(gate.qubits[0], theta=0.3)
        return _as_basis_1q(gate)

    monkeypatch.setattr(
        "qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass._as_basis_1q",
        patched_as_basis,
    )
    out = _sqrt_1q_gate_as_basis(WrapperGate(0))
    assert isinstance(out, RX)


def test_single_and_multi_controlled_paths():
    rz_seq = _single_controlled(1, RZ(0, phi=0.2))
    rx_seq = _single_controlled(1, RX(0, theta=0.2))
    ry_seq = _single_controlled(1, RY(0, theta=0.2))
    u3_seq = _single_controlled(1, U3(0, theta=0.3, phi=0.2, gamma=-0.1))
    dummy_gate = DummyBasicGate((5,), np.eye(2))
    recursive_seq = _single_controlled(1, dummy_gate)

    assert _count_gate_names(rz_seq)["CZ"] >= 1
    assert _count_gate_names(rx_seq)["CZ"] >= 1
    assert _count_gate_names(ry_seq)["CZ"] >= 1
    assert _count_gate_names(u3_seq)["CZ"] >= 1
    assert _count_gate_names(recursive_seq)["CZ"] >= 1

    base_rotation = RX(3, theta=0.2)
    no_ctrl = _multi_controlled([], base_rotation)
    one_ctrl = _multi_controlled([1], base_rotation)
    two_ctrls = _multi_controlled([1, 2], base_rotation)

    assert no_ctrl == [base_rotation]
    assert _count_gate_names(one_ctrl)["CZ"] >= 1
    assert _count_gate_names(two_ctrls)["CZ"] >= 1


def test_rewrite_gate_covers_various_cases():
    pass_instance = CircuitToCanonicalBasisPass()

    gates = [
        M(0),
        U3(0, theta=0.1, phi=0.2, gamma=0.3),
        RX(0, theta=0.2),
        RY(0, theta=0.3),
        RZ(0, phi=0.4),
        CZ(0, 1),
        I(0),
        H(0),
        X(0),
        Y(0),
        Z(0),
        U1(0, phi=0.5),
        U2(0, phi=0.6, gamma=0.7),
        CNOT(0, 1),
        SWAP(0, 1),
    ]

    seqs = [pass_instance._rewrite_gate(g) for g in gates]

    assert len(seqs[0]) == 1 and seqs[0][0].name == "M"
    assert len(seqs[5]) == 1 and seqs[5][0].name == "CZ"
    assert seqs[6] == []
    assert len(seqs[7]) == 1 and seqs[7][0].name == "U3"
    assert len(seqs[8]) == 1 and seqs[8][0].name == "RX"
    assert len(seqs[9]) == 1 and seqs[9][0].name == "RY"
    assert len(seqs[10]) == 1 and seqs[10][0].name == "RZ"
    assert len(seqs[11]) == 1 and seqs[11][0].name == "RZ"
    assert len(seqs[12]) == 1 and seqs[12][0].name == "U3"
    assert _count_gate_names(seqs[13])["CZ"] == 1
    assert _count_gate_names(seqs[14])["CZ"] == 3


def test_rewrite_gate_handles_controlled_and_adjoint(monkeypatch):
    pass_instance = CircuitToCanonicalBasisPass()

    base_gate = DummyBasicGate((2,), np.eye(2))

    def fake_as_basis(gate):
        if gate is base_gate:
            return U3(5, theta=0.1, phi=0.2, gamma=0.3)
        return _as_basis_1q(gate)

    monkeypatch.setattr(
        "qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass._as_basis_1q",
        fake_as_basis,
    )

    controlled = Controlled(0, 1, basic_gate=base_gate)
    adjoint_gate = Adjoint(RX(0, theta=math.pi / 3))
    expo_gate = RX(0, theta=math.pi / 4).exponential()
    basic_gate = DummyBasicGate((0,), np.eye(2))

    ctrl_seq = pass_instance._rewrite_gate(controlled)
    adj_seq = pass_instance._rewrite_gate(adjoint_gate)
    exp_seq = pass_instance._rewrite_gate(expo_gate)
    basic_seq = pass_instance._rewrite_gate(basic_gate)

    assert _count_gate_names(ctrl_seq)["CZ"] >= 1
    assert _count_gate_names(adj_seq)["RX"] >= 1
    assert len(exp_seq) == 1 and exp_seq[0].name == "U3"
    assert len(basic_seq) == 1 and basic_seq[0].name == "U3"
    assert all(5 not in g.qubits for g in ctrl_seq)

    multi_qubit_controlled = Controlled(0, basic_gate=DummyBasicGate((1, 2), np.eye(4)))
    exponential_multi = Exponential(DummyBasicGate((0, 1), np.eye(4)))

    with pytest.raises(NotImplementedError):
        pass_instance._rewrite_gate(multi_qubit_controlled)
    with pytest.raises(NotImplementedError):
        pass_instance._rewrite_gate(exponential_multi)


def test_canonical_pass_run_produces_basis_circuit():
    circuit = Circuit(3)
    circuit.add(CNOT(0, 1))
    circuit.add(SWAP(1, 2))
    circuit.add(Adjoint(RY(2, theta=0.5)))
    circuit.add(RX(0, theta=0.3))

    pass_instance = CircuitToCanonicalBasisPass()
    out = pass_instance.run(circuit)

    assert all(g.name in {"CZ", "U3", "RX", "RY", "RZ"} for g in out.gates)
    assert len(out.gates) > 0
