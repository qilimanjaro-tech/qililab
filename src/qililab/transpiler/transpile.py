from gate_decompositions import native_gates, translate_gate
from qibo import gates
from qibo.config import log
from qibo.models import Circuit


def translate_circuit(circuit):
    """Translates a circuit to native gates
    Returns a new circuit
    """

    ngates = circuit.queue
    new_circuit = Circuit(circuit.nqubits)

    new_circuit.add(translate_gate(ngates))
    return new_circuit
