import numpy as np

from qililab.digital.native_gates import Drag, _GateHandler
from qibo import Circuit, gates


def test_native_gates_drag():
    """Test drag pulse native gate"""

    drag_gate = Drag(0, 0, 0)  # initialize gate

    assert isinstance(drag_gate, Drag)
    assert drag_gate.name == "drag"
    assert len(drag_gate.parameters) == 2
    assert drag_gate.parameter_names == ["theta", "phase"]
    assert drag_gate.trainable is True

    # try different parameters
    rng = np.random.default_rng(seed=42)  # init random number generator
    for _ in range(50):
        theta = rng.random()
        phi = rng.random()
        qubit = rng.integers(0, 100)
        drag_gate = Drag(qubit, theta, phi)  # initialize gate
        assert drag_gate.parameters == (theta, phi)
        assert drag_gate.qubits == qubit

def test_normalize_angle():
    """Test normalize angle."""
    assert _GateHandler.normalize_angle(3 * np.pi) == np.pi
    assert _GateHandler.normalize_angle(2 * np.pi) == 0
    assert _GateHandler.normalize_angle(3/2 * np.pi) == - np.pi/2
    assert _GateHandler.normalize_angle(np.pi) == np.pi
    assert _GateHandler.normalize_angle(np.pi / 2) == np.pi / 2

def test_get_circuit_gates_info():
    """Test get circuit gates."""
    circuit = Circuit(2)
    circuit.add(gates.X(0))
    circuit.add(gates.H(1))

    circuit_gates_info = _GateHandler.get_circuit_gates_info(circuit.queue)

    assert circuit_gates_info == [("X", [0], {}), ("H", [1], {})]

def test_create_gate():
    """Test create gate."""
    gate = _GateHandler.create_gate("X", [0], {})
    assert isinstance(gate, gates.X)
    assert gate.init_args == [0]

def test_create_circuit():
    """Test create circuit."""
    circuit_gates = [("X", [0], {}), ("H", [1], {})]
    circuit_gates = _GateHandler.create_qibo_gates_from_gates_info(circuit_gates)

    assert len(circuit_gates) == 2
    assert [gate.name for gate in circuit_gates] == ["x", "h"]


def test_create_circuit_from_gates():
    """Test create circuit from gates."""
    gates_list = [gates.X(0), gates.H(1)]
    nqubits = 2
    wire_names = [0, 1]

    circuit = _GateHandler.create_circuit_from_gates(gates_list, nqubits, wire_names)

    assert len(circuit.queue) == 2
    assert [gate.name for gate in circuit.queue] == ["x", "h"]
    assert circuit.wire_names == [0, 1]

def test_extract_qubits():
    """Test extract qubits."""
    qubits = _GateHandler.extract_qubits_from_gate_args([0, 1])
    assert qubits == [0, 1]

    qubits = _GateHandler.extract_qubits_from_gate_args(0)
    assert qubits == [0]
