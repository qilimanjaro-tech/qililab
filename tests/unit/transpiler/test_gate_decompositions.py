import pytest
from qibo import gates

from qililab.transpiler.gate_decompositions import GateDecompositions, native_gates, translate_gates


@pytest.fixture(name="test_gates")
def get_gates() -> list[gates.Gate]:
    test_gates = [gates.X(0), gates.CNOT(0, 1), gates.RY(0, 2.5)]
    return test_gates


def test_GateDecompositions(test_gates: gates.Gate):
    """Test that class GateDecompositions creates a dictionary of gate translations

    Args:
        test_gates (gates.Gate): list of gates to be translated
    """
    decomp = GateDecompositions()
    # add some fake decompositions
    decomp.add(gates.RY, lambda gate: [gates.U3(0, gate.parameters[0], 2, 0)])
    decomp.add(gates.X, [gates.Y(0)])
    decomp.add(gates.CNOT, lambda gate: [gates.SWAP(0, 1)])

    assert isinstance(decomp.decompositions, dict)
    for gate in test_gates:
        assert isinstance(decomp(gate)[0], gates.Gate)


def test_translate_gates(test_gates: gates.Gate):
    """Test that translate gates outputs a list of gates as expected

    Args:
        test_gates (gates.Gate): list of gates to be translated
    """

    tr_gates = translate_gates(test_gates)
    assert isinstance(tr_gates, list)
    for gate in tr_gates:
        assert isinstance(gate, gates.Gate)


def test_native_gates():
    """Test native gates output is a set of gates"""

    for gate in native_gates():
        assert isinstance(gate, gates.Gate)
