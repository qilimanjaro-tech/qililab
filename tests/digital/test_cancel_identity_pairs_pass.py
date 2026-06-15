import math
from typing import Any, TYPE_CHECKING, ClassVar

import numpy as np
import pytest
from qilisdk.digital import (
    CNOT,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Circuit,
    Gate,
    H,
    I,
    X,
)
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qilisdk.digital.gates import Adjoint, Controlled, M, BasicGate
from qilisdk.digital.gates import _process_param

from qililab.digital.circuit_transpiler_passes.cancel_identity_pairs_pass import (
    CancelIdentityPairsPass,
    _dephased_signature,
    _first_nonzero_phase,
    _try_matrix,
)


def describe_gates(circuit: Circuit) -> list[tuple[str, tuple[int, ...], tuple[float, ...]]]:
    """Return a succinct description of the circuit gates for assertions."""

    snapshot: list[tuple[str, tuple[int, ...], tuple[float, ...]]] = []
    for gate in circuit.gates:
        snapshot.append((type(gate).__name__, gate.qubits, tuple(gate.get_parameter_values())))
    return snapshot


class PhaseGate(BasicGate):
    """Simple one-qubit gate used to exercise the matrix fallback."""
    PARAMETER_NAMES: ClassVar[list[str]] = ["phase"]

    def __init__(self, qubit: int, *, phase: float) -> None:
        params_to_init = {}
        terms_to_init = {}

        # Process the parameters
        _process_param("phase", phase, params_to_init, terms_to_init)

        # Initialize the base class
        super().__init__(
            target_qubits=(qubit,),
            parameters=params_to_init,
            parameter_transforms=terms_to_init,
        )

    @property
    def name(self) -> str:  # pragma: no cover - required by abstract base but unused
        return "PhaseGate"
    
    @property
    def phase(self) -> float:
        if "phase" in self._parameter_transforms:
            val = self._parameter_transforms["phase"].evaluate({})
            if isinstance(val, complex):
                return val.real
            return val
        return self.get_parameters()["phase"]
    
    def _generate_matrix(self) -> np.ndarray:
        return np.array([[1.0, 0.0], [0.0, np.exp(1j * self.phase)]], dtype=complex)


class NoMatrixGate(BasicGate):
    """Gate without a matrix to trigger the barrier path."""

    PARAMETER_NAMES: ClassVar[list[str]] = []

    def __init__(self, qubit: int,) -> None:
        params_to_init = {}
        terms_to_init = {}

        # Initialize the base class
        super().__init__(
            target_qubits=(qubit,),
            parameters=params_to_init,
            parameter_transforms=terms_to_init,
        )

    @property
    def name(self) -> str:  # pragma: no cover - required by abstract base but unused
        return "NoMatrixGate"

    def _generate_matrix(self) -> np.ndarray:
        raise GateHasNoMatrixError


class TestCancelIdentityPairsPass:
    def test_involutions_and_identity_are_removed(self) -> None:
        circuit = Circuit(2)
        circuit.add(H(0))
        circuit.add(H(0))
        circuit.add(CZ(1, 0))
        circuit.add(CZ(0, 1))
        circuit.add(SWAP(0, 1))
        circuit.add(SWAP(1, 0))
        circuit.add(X(0))
        circuit.add(X(0))
        circuit.add(I(1))

        result = CancelIdentityPairsPass().run(circuit)

        assert describe_gates(result) == []
        # Original circuit remains untouched
        assert len(circuit.gates) == 9

    def test_parameterized_rotations_cancel_with_wrapped_angles(self) -> None:
        circuit = Circuit(1)
        circuit.add(RX(0, theta=math.pi / 2))
        circuit.add(RX(0, theta=3 * math.pi / 2))  # wraps to -pi/2
        circuit.add(RY(0, theta=math.pi / 4))
        circuit.add(RY(0, theta=-math.pi / 4))
        circuit.add(RZ(0, phi=0.0))
        circuit.add(RZ(0, phi=0.0))
        circuit.add(U1(0, phi=0.3))
        circuit.add(U1(0, phi=-0.3))

        result = CancelIdentityPairsPass().run(circuit)

        assert describe_gates(result) == []

    def test_u_gate_cancellations(self) -> None:
        circuit = Circuit(1)
        circuit.add(U2(0, phi=0.5, gamma=1.2))
        circuit.add(U3(0, theta=-math.pi / 2, phi=-1.2, gamma=-0.5))  # inverse of U2 above
        circuit.add(U3(0, theta=0.9, phi=0.1, gamma=0.7))
        circuit.add(U3(0, theta=-0.9, phi=-0.7, gamma=-0.1))
        circuit.add(U3(0, theta=0.9, phi=0.1, gamma=0.7))

        result = CancelIdentityPairsPass().run(circuit)

        # Only the unmatched trailing U3 should remain
        assert describe_gates(result) == [("U3", (0,), (0.9, 0.1, 0.7))]

    def test_adjoint_and_controlled_pairs_cancel(self) -> None:
        circuit = Circuit(2)
        circuit.add(Adjoint(RX(0, theta=0.6)))
        circuit.add(RX(0, theta=0.6))
        circuit.add(Controlled(1, basic_gate=RY(0, theta=0.2)))
        circuit.add(Controlled(1, basic_gate=RY(0, theta=-0.2)))

        result = CancelIdentityPairsPass().run(circuit)

        assert describe_gates(result) == []

    def test_matrix_fallback_cancels_custom_unitaries(self) -> None:
        circuit = Circuit(2)
        circuit.add(PhaseGate(0, phase=0.4))
        circuit.add(PhaseGate(1, phase=0.1))
        circuit.add(PhaseGate(0, phase=-0.4))

        result = CancelIdentityPairsPass().run(circuit)

        assert describe_gates(result) == [("PhaseGate", (1,), (0.1,))]

    def test_measurements_and_unknown_gates_block_cancellation(self) -> None:
        circuit = Circuit(1)
        circuit.add(X(0))
        circuit.add(M(0))
        circuit.add(X(0))  # blocked by measurement
        circuit.add(X(0))
        circuit.add(NoMatrixGate(0))  # clears pending candidate
        circuit.add(X(0))

        result = CancelIdentityPairsPass().run(circuit)

        # Measurement prevents the first pair from cancelling, but the last two X cancel
        assert describe_gates(result) == [
            ("X", (0,), tuple()),
            ("M", (0,), tuple()),
            ("NoMatrixGate", (0,), tuple()),
            ("X", (0,), tuple()),
        ]

    def test_first_nonzero_phase_and_dephased_signature(self) -> None:
        matrix = np.diag([1.0, np.exp(1j * 0.3)])
        phased_matrix = np.exp(1j * 0.7) * matrix

        assert math.isclose(_first_nonzero_phase(phased_matrix), 0.7, rel_tol=1e-9)
        assert _dephased_signature(matrix) == _dephased_signature(phased_matrix)
        assert _dephased_signature(np.array([])) == ()

    def test_try_matrix_handles_missing_matrix(self) -> None:
        assert isinstance(_try_matrix(CZ(0, 1)), np.ndarray)
        assert _try_matrix(M(0)) is None

    def test_qubits_key_and_blocking(self) -> None:
        pass_obj = CancelIdentityPairsPass()
        assert pass_obj._qubits_key(CZ(3, 1)) == (1, 3)
        assert pass_obj._qubits_key(SWAP(5, 2)) == (2, 5)
        assert pass_obj._qubits_key(CNOT(2, 0)) == (2, 0)

        stack: dict[tuple[Any, tuple[int, ...]], int] = {
            (("INV", "X"), (0,)): 1,
            (("INV", "X"), (1,)): 2,
        }

        pass_obj._block_overlapping(stack, ())  # clears everything
        assert stack == {}

        stack = {
            (("INV", "X"), (0,)): 1,
            (("INV", "X"), (1,)): 2,
        }

        pass_obj._block_overlapping(stack, (1,))
        assert stack == {(("INV", "X"), (0,)): 1}
