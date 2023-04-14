import cirq
import numpy as np
import pytest
import qibo
from apply_circuit import apply_circuit
from qibo import gates
from qibo.models import Circuit
from transpile import translate_circuit

qibo.set_backend("numpy")  # set backend to numpy (this is the faster option for < 15 qubits)


def compare_circuits(circuit_q: Circuit, circuit_t: Circuit, nqubits: int) -> float:
    """Runs same circuit using transpiled gates and qibo gates,
    and calculates the scalar product of the 2 resulting states

    Inputs
    circuit_q: qibo circuit
    circuit_t: transpiled circuit
    nqubits :number of qubits
    Outputs
    scalar product of 2 states (real value)
    """

    # get final state
    state_q = circuit_q().state()
    state_t = apply_circuit(circuit_t)

    # if state_t = k*state_q, where k is a global phase
    # then |state_q * state_t| = |state_q * state_q| * |k| = 1
    return np.abs(np.dot(np.conjugate(state_t), state_q))


def test_transpiler():
    """Test that the transpiled circuit outputs same result if
    circuits are the same, and different results if circuits are
    not the same
    """

    # circuits are the same
    for i in range(0, 1000):
        nqubits = np.random.randint(4, 10)
        c1 = Circuit.from_qasm(cirq.testing.random_circuit(qubits=nqubits, n_moments=10, op_density=1).to_qasm())
        c2 = translate_circuit(c1)

        if not np.allclose(1, compare_circuits(c1, c2, nqubits)):
            raise Exception("final states differ!")

    # circuits are not the same
    for i in range(0, 200):
        nqubits = np.random.randint(4, 10)
        c1 = Circuit.from_qasm(cirq.testing.random_circuit(qubits=nqubits, n_moments=10, op_density=1).to_qasm())
        c2 = Circuit.from_qasm(cirq.testing.random_circuit(qubits=nqubits, n_moments=10, op_density=1).to_qasm())
        c2 = translate_circuit(c2)

        if np.allclose(1, compare_circuits(c1, c2, nqubits)):
            raise Exception("final states differ!")
