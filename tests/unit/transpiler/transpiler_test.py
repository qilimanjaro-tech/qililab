import numpy as np
import pytest
import qibo
from qibo import gates
from qibo.backends import NumpyBackend
from qibo.models import Circuit

from qililab.transpiler import translate_circuit

qibo.set_backend("numpy")  # set backend to numpy (this is the faster option for < 15 qubits)


def random_circuit(
    nqubits: int, ngates: int, rng: np.random.Generator, gates_list: list[qibo.gates.Gate] = None, exhaustive=False
) -> Circuit:
    """Generates random qibo circuit with ngates

    Args:
        nqubits (int): number of qubits in the circuit
        ngates (int): number of gates in the circuit
        gates_list (dict[gates:int]): dictionary with gates and amount of qubits where those should be applied
        exhaustive (bool) : use all gates at least once (requires ngates>=len(gates))

    Returns:
        c (qibo.Circuit) : resulting circuit
    """

    # get list available gates
    if gates_list is None:
        gates_list = get_default_gates()

    # init circuit
    c = Circuit(nqubits)

    # get list of gates to use
    if not exhaustive:
        gates = rng.choice(gates_list, ngates)
    # if exhaustive = True then add all the gates available
    else:
        if ngates < len(gates_list):
            raise Exception("If exhaustive is set to True then ngates must be bigger than len(gates_list)!")
        gates = []
        for k in range(ngates // len(gates_list)):
            gates.extend(gates_list)
        gates.extend(rng.choice(gates_list, ngates % len(gates_list), replace=False))
        rng.shuffle(gates)

    # add gates iteratively
    for gate in gates:
        # apply gate to random qubits
        new_qubits = rng.choice([i for i in range(0, nqubits)], len(gate.qubits), replace=False)
        gate = gate.on_qubits({i: q for i, q in enumerate(new_qubits)})
        if (len(gate.parameters) != 0) and gate.name != "id":
            new_params = tuple([1 for param in range(len(gate.parameters))])
            gate.parameters = new_params
        c.add(gate)

    return c


def get_default_gates():
    """Get list of transpilable gates. Gates are initialized so properties can be accessed

    Returns:
        default_gates: (list[gates.Gate])
    """
    # init gates
    default_gates = [
        gates.I(0),
        gates.X(0),
        gates.Y(0),
        gates.Z(0),
        gates.H(0),
        gates.RX(0, 0),
        gates.RY(0, 0),
        gates.RZ(0, 0),
        gates.U1(0, 0),
        gates.U2(0, 0, 0),
        gates.U3(0, 0, 0, 0),
        gates.S(0),
        gates.SDG(0),
        gates.T(0),
        gates.TDG(0),
        gates.CNOT(0, 1),
        gates.CZ(0, 1),
        gates.SWAP(0, 1),
        gates.iSWAP(0, 1),
        gates.CRX(0, 1, 0),
        gates.CRY(0, 1, 0),
        gates.CRZ(0, 1, 0),
        gates.CU1(0, 1, 0),
        gates.CU2(0, 1, 0, 0),
        gates.CU3(0, 1, 0, 0, 0),
        gates.FSWAP(0, 1),
        gates.RXX(0, 1, 0),
        gates.RYY(0, 1, 0),
        gates.RZZ(0, 1, 0),
        gates.TOFFOLI(0, 1, 2),
    ]
    return default_gates


def apply_circuit(circuit: Circuit) -> np.ndarray:
    """Apply native gates from a transpiled circuit
    Drag pulses are translated to supported qibo.gates RX, RZ.
    Gates are applied onto initial state |00...0>
    Backend is set to numpy for faster execution since circuits are small

    Args:
        circuit (Circuit): transpiled qibo circuit to be executed

    Returns:
        state (np.ndarray): resulting state
    """

    backend = NumpyBackend()

    nqubits = circuit.nqubits
    # start initial state |00...0>
    state = np.zeros(2**nqubits)
    state[0] = 1
    for gate in circuit.queue:
        if gate.name == "rz":
            state = backend.apply_gate(gate, state, nqubits)
        if gate.name == "drag":
            theta = gate.parameters[0]
            phi = gate.parameters[1]
            qubit = gate.qubits[0]
            # apply Drag gate as RZ and RX gates
            state = backend.apply_gate(gates.RZ(qubit, -phi), state, nqubits)
            state = backend.apply_gate(gates.RX(qubit, theta), state, nqubits)
            state = backend.apply_gate(gates.RZ(qubit, phi), state, nqubits)

        if gate.name == "cz":
            state = backend.apply_gate(gate, state, nqubits)

    return state


def compare_circuits(circuit_q: Circuit, circuit_t: Circuit, nqubits: int) -> float:
    """Runs same circuit using transpiled gates and qibo gates,
    and calculates the scalar product of the 2 resulting states

    Args:
        circuit_q (Circuit): qibo circuit (not transpiled)
        circuit_t (Circuit): transpiled qibo circuit
        nqubits (int): number of qubits in the circuit

    Returns:
        float: absolute scalar product of the 2 resulting states from circuit execution
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
    rng = np.random.default_rng(seed=42)  # init random number generator

    # circuits are the same
    for i in range(0, 1000):
        nqubits = np.random.randint(4, 10)
        c1 = random_circuit(
            nqubits=5,
            ngates=len(get_default_gates()),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = translate_circuit(c1)
        if not np.allclose(1, compare_circuits(c1, c2, nqubits)):
            raise Exception("final states differ!")

    # circuits are not the same
    for i in range(0, 200):
        nqubits = np.random.randint(4, 10)
        c1 = random_circuit(
            nqubits=5,
            ngates=len(get_default_gates()),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = random_circuit(
            nqubits=5,
            ngates=len(get_default_gates()),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = translate_circuit(c2)

        if np.allclose(1, compare_circuits(c1, c2, nqubits)):
            raise Exception("final states differ!")
