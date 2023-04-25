import numpy as np
import pytest
import qibo
from qibo import gates
from qibo.backends import NumpyBackend
from qibo.models import Circuit

from qililab.transpiler import translate_circuit
from qililab.transpiler.native_gates import Drag
from qililab.transpiler.transpiler import optimize_transpilation

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
        gates_list = default_gates

    # init circuit
    c = Circuit(nqubits)

    # get list of gates to use
    if not exhaustive:
        list_gates = rng.choice(gates_list, ngates)
    # if exhaustive = True then add all the gates available
    else:
        if ngates < len(gates_list):
            raise Exception("If exhaustive is set to True then ngates must be bigger than len(gates_list)!")
        list_gates = []  # TODO change name so it does not match gates from qibo.gates
        for k in range(ngates // len(gates_list)):
            list_gates.extend(gates_list)
        list_gates.extend(rng.choice(gates_list, ngates % len(gates_list), replace=False))
        rng.shuffle(list_gates)

    # add gates iteratively
    for gate in list_gates:
        # apply gate to random qubits
        new_qubits = rng.choice([i for i in range(0, nqubits)], len(gate.qubits), replace=False)
        gate = gate.on_qubits({i: q for i, q in enumerate(new_qubits)})
        if (len(gate.parameters) != 0) and gate.name != "id":
            new_params = tuple([1 for param in range(len(gate.parameters))])
            gate.parameters = new_params
        c.add(gate)

    return c


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


def compare_exp_z(circuit_q: Circuit, circuit_t: Circuit, nqubits: int) -> list[np.ndarray]:
    """Runs same circuit using transpiled gates and qibo gates, applies Z operator to all qubits
    and then calculates the modulo of each coefficient of the state vector. This last operation
    removes the phase difference in Z so that if the state vectors have the same Z observables
    then the state vector coefficients will be the same.
    That is, for the state vector psi, psi' for the transpiled and qibo circuits
    .. math:: \Psi_k == \Psi'_k \forall k
    Where each psi_k is the coefficient of each basis of the 2^n dimensional state vector
    representation in Z

    Args:
        circuit_q (Circuit): qibo circuit (not transpiled)
        circuit_t (Circuit): transpiled qibo circuit
        nqubits (int): number of qubits in the circuit

    Returns:
        list[np.ndarray]: a list with 2 arrays, one corresponding to the state vector for the
            transpiled circuit and another one for the qibo circuit
    """

    # get final states and save them for modulo calculation
    state_q = circuit_q().state()
    state_q_0 = state_q.copy()
    state_t = apply_circuit(circuit_t)
    state_t_0 = state_t.copy()

    # apply measurement in Z
    backend = NumpyBackend()
    for q in range(circuit_q.nqubits):
        state_q = backend.apply_gate(gates.Z(q), state_q, circuit_q.nqubits)
        state_t = backend.apply_gate(gates.Z(q), state_t, circuit_q.nqubits)

    return [
        np.array([i * k for i, k in zip(np.conjugate(state_t_0), state_t)]),
        np.array([i * k for i, k in zip(np.conjugate(state_q_0), state_q)]),
    ]


def test_translate_gates():
    """Tests the translate_gates function without optimization
    Test that the transpiled circuit outputs same result if
    circuits are the same, and different results if circuits are
    not the same. State vectors should be the same up to a global
    phase difference
    """
    rng = np.random.default_rng(seed=42)  # init random number generator

    # circuits are the same
    for i in range(0, 500):
        nqubits = np.random.randint(4, 10)
        c1 = random_circuit(
            nqubits=nqubits,
            ngates=len(default_gates),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )

        c2 = translate_circuit(c1)

        # check that both c1, c2 are qibo.Circuit
        assert isinstance(c1, Circuit)
        assert isinstance(c2, Circuit)

        # check that states are equivalent up to a global phase
        assert np.allclose(1, compare_circuits(c1, c2, nqubits))

    # circuits are not the same
    for i in range(0, 50):
        nqubits = np.random.randint(4, 10)
        c1 = random_circuit(
            nqubits=nqubits,
            ngates=len(default_gates),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = random_circuit(
            nqubits=nqubits,
            ngates=len(default_gates),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = translate_circuit(c2)

        # check that both c1, c2 are qibo.Circuit
        assert isinstance(c1, Circuit)
        assert isinstance(c2, Circuit)

        # check that states differ
        assert not np.allclose(1, compare_circuits(c1, c2, nqubits))


def test_optimize_transpilation():
    """Test that optimize_transpilation behaves as expected"""
    # gate list to optimize
    test_gates = [
        Drag(0, 1, 1),
        gates.CZ(0, 1),
        gates.RZ(1, 1),
        gates.M(0),
        gates.RZ(0, 2),
        Drag(0, 3, 3),
        gates.CZ(0, 2),
        Drag(1, 2, 3),
        gates.RZ(1, 0),
    ]
    # resulting gate list from optimization
    result_gates = [Drag(0, 1, 1), gates.CZ(0, 1), gates.M(0), Drag(0, 3, 1), gates.CZ(0, 2), Drag(1, 2, 2)]

    # check that lists are the same
    optimized_gates = optimize_transpilation(3, test_gates)
    for gate_r, gate_opt in zip(result_gates, optimized_gates):
        assert gate_r.name == gate_opt.name
        assert gate_r.parameters == gate_opt.parameters


def test_transpiler():
    """Test full transpilation of a circuit
    (transpilation + optimization)
    """
    rng = np.random.default_rng(seed=42)  # init random number generator

    # circuits are the same
    for i in range(0, 500):
        nqubits = np.random.randint(4, 10)
        c1 = random_circuit(
            nqubits=nqubits,
            ngates=len(default_gates),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )

        c2 = translate_circuit(c1, True)

        # check that both c1, c2 are qibo.Circuit
        assert isinstance(c1, Circuit)
        assert isinstance(c2, Circuit)

        # check that states have the same absolute coefficients
        z1_exp, z2_exp = compare_exp_z(c1, c2, nqubits)
        assert np.allclose(z1_exp, z2_exp)

    # circuits are not the same
    for i in range(0, 50):
        nqubits = np.random.randint(4, 10)
        c1 = random_circuit(
            nqubits=nqubits,
            ngates=len(default_gates),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = random_circuit(
            nqubits=nqubits,
            ngates=len(default_gates),
            rng=rng,
            gates_list=None,
            exhaustive=True,
        )
        c2 = translate_circuit(c2, True)

        # check that both c1, c2 are qibo.Circuit
        assert isinstance(c1, Circuit)
        assert isinstance(c2, Circuit)

        # check that states have the same absolute coefficients
        z1_exp, z2_exp = compare_exp_z(c1, c2, nqubits)
        # print(z1_exp, z2_exp)
        assert not np.allclose(z1_exp, z2_exp)


# transpilable gates
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
