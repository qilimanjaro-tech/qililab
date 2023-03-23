from qibo import gates
from qibo.models.circuit import Circuit as QiboCircuit

from qililab.circuit import Circuit
from qililab.circuit.operations import Operation

# TODO: We must investigate the various decompositions of Qili operations and Qibo gates
# A nice reference is the transpilers module of Qibolab


class QiboConverter:
    @staticmethod
    def to_qibo(circuit: Circuit) -> QiboCircuit:
        qibo_circuit = QiboCircuit(circuit.num_qubits)
        return qibo_circuit

    @staticmethod
    def from_qibo(circuit: QiboCircuit) -> Circuit:
        qili_circuit = Circuit(circuit.nqubits)
        return qili_circuit
