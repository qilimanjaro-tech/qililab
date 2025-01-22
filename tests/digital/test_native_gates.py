import numpy as np

from qililab.digital.native_gates import Drag, normalize_angle


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
    assert normalize_angle(3 * np.pi) == np.pi
    assert normalize_angle(2 * np.pi) == 0
    assert normalize_angle(3/2 * np.pi) == - np.pi/2
    assert normalize_angle(np.pi) == np.pi
    assert normalize_angle(np.pi / 2) == np.pi / 2
