import numpy as np

from qililab.digital.native_gates import Drag, _GateHandler, Wait
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

    assert circuit_gates_info == [gates.X(0).raw, gates.H(1).raw]
    assert gates.X(0).raw == {
        "_class": "X",
        "init_args": [0],
        "init_kwargs": {},
        "name": "x",
        "_control_qubits": (),
        "_target_qubits": (0,)
    }

def test_native_gates_raw():
    """Test native gates raw."""
    drag_gate = Drag(0, 0, 0)
    assert drag_gate.raw == {
        "_class": "Drag",
        "init_args": [0],
        "init_kwargs": {
            'phase': 0,
            'theta': 0,
            'trainable': True
        },
        "name": "drag",
        "_control_qubits": (),
        "_target_qubits": (0,)
    }

    wait_gate = Wait(0, 100)
    assert wait_gate.raw == {
        "_class": "Wait",
        "init_args": [0],
        "init_kwargs": {"t": 100},
        "name": "wait",
        "_control_qubits": (),
        "_target_qubits": (0,)
    }

def test_create_gate():
    """Test create gate."""
    gate = _GateHandler.create_gate(gates.X(0).raw)
    assert isinstance(gate, gates.X)
    assert gate.init_args == [0]

def test_create_circuit():
    """Test create circuit."""
    circuit_gates = [gates.X(0).raw, gates.H(1).raw]
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
