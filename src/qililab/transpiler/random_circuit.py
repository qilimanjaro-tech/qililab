import numpy as np
import qibo
from qibo import gates
from qibo.models import Circuit


def random_circuit(
    nqubits: int, ngates: int, rng: np.random.Generator, gates_list: list[qibo.gates.Gate] = None, exhaustive=False
) -> Circuit:
    """Generates random qibo circuit with ngates

    Args:
    nqubits (int)   : number of qubits in the circuit
    ngates (int)    : number of gates in the circuit
    gates_list (dict(gates, int))    : dictionary with gates and amount of qubits where those should be applied
    exhaustive (bool) : use all gates at least once (requires ngates>=len(gates))

    Out:
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

    Out:
    default_gates (list[gates])
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
