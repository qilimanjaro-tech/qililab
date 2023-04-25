from qibo import gates
from qibo.config import log
from qibo.models import Circuit

from qililab.transpiler.gate_decompositions import translate_gates


def translate_circuit(circuit: Circuit) -> Circuit:
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
    # add transpiled gates to new circuit
    new_circuit.add(translate_gates(ngates))

    return new_circuit
