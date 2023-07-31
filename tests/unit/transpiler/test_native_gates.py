import numpy as np

from qililab.transpiler.native_gates import Drag


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
