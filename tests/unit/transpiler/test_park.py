from qililab.transpiler.park_gate import Park


def test_park_gate():
    """Test drag pulse native gate"""

    park_gate = Park(0)  # initialize gate

    assert isinstance(park_gate, Park)
    assert park_gate.name == "park"
    assert len(park_gate.parameters) == 0
    assert park_gate.qubits[0] == 0
    assert len(park_gate.qubits) == 1
