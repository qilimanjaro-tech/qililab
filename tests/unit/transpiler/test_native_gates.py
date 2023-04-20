from qililab.transpiler.native_gates import Drag


def test_native_gates_drag():
    """Test drag pulse native gate"""

    drag_gate = Drag(0, 0, 0)  # initialize gate

    assert isinstance(drag_gate, Drag)
    assert drag_gate.name == "drag"
    assert len(drag_gate.parameters) == 2
