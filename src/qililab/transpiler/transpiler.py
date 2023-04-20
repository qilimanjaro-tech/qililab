from qibo import gates
from qibo.config import log
from qibo.models import Circuit

from qililab.transpiler.gate_decompositions import translate_gates


def translate_circuit(circuit: Circuit, optimize: bool = False) -> Circuit:
    """Converts circuit with qibo gates to circuit with native gates

    Args:
        circuit (Circuit): circuit with qibo gates

    Returns:
        new_circuit (Circuit): circuit with transpiled gates
    """
    # get list of gates from circuit
    ngates = circuit.queue
    # init new circuit
    new_circuit = Circuit(circuit.nqubits)
    # add transpiled gates to new circuit, optimize if needed
    if optimize:
        gates_to_optimize = translate_gates(ngates)
        new_circuit.add(optimize_transpilation(circuit.nqubits, gates_to_optimize))
    else:
        new_circuit.add(translate_gates(ngates))

    return new_circuit


def optimize_transpilation(nqubits: int, ngates: list[gates.Gate]) -> list[gates.Gate]:
    """Optimizes transpiled circuit by moving all RZ to the left as a single RZ

    Args:
        nqubits
        ngates

    Out:
        list[gates.Gate]
    """
    # TODO: we are ignoring measurement gates so far (i.e. treating them as an identity)
    supported_gates = ["rz", "drag", "cz", "measure"]
    new_gates = []
    shift = {qubit: 0 for qubit in range(nqubits)}
    # TODO: check that the order is right
    for gate in ngates:
        if gate.name not in supported_gates:
            raise Exception(f"{gate.name} not part of supported gates {supported_gates}")
        if gate.name == "rz":
            shift[gate.qubits[0]] += gate.parameters[0]
        else:
            # if gate is drag pulse, shift parameters by accumulated Zs
            if gate.name == "drag":
                gate.parameters = (gate.parameters[0], gate.parameters[1] - shift[gate.qubits[0]])
            new_gates.append(gate)
    # add shifts in z as one

    for qubit in shift.keys():
        new_gates.append(gates.RZ(qubit, shift[qubit]))

    return new_gates
