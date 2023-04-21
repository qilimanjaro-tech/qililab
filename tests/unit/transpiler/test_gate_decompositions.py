import numpy as np
import pytest
from qibo import gates

from qililab.transpiler.gate_decompositions import GateDecompositions, native_gates, translate_gates
from qililab.transpiler.native_gates import Drag


@pytest.fixture(name="test_gates")
def get_gates() -> list[gates.Gate]:
    test_gates = [gates.X(0), gates.CNOT(0, 1), gates.RY(0, 2.5)]
    return test_gates


@pytest.fixture(name="decomposed_gates")
def test_GateDecompositions(test_gates: list[gates.Gate]):
    """Test that class GateDecompositions creates a dictionary of gate translations

    Args:
        test_gates (list[gates.Gate]): list of gates to be translated
        decomposed_gates (list[gates.Gate]) : corresponding decomposition for test_gates
    """
    decomp = GateDecompositions()
    # add some fake decompositions
    decomp.add(gates.RY, lambda gate: [gates.U3(0, gate.parameters[0], 2, 0)])
    decomp.add(gates.X, [gates.Y(0)])
    decomp.add(gates.CNOT, lambda gate: [gates.SWAP(0, 1)])

    # decomposed gates from fixture should look like this
    decomposed_gates = [gates.Y(0), gates.SWAP(0, 1), gates.U3(0, 2.5, 2, 0)]

    assert isinstance(decomp.decompositions, dict)
    for gate, test_dec_gate in zip(test_gates, decomposed_gates):
        dec_gate = decomp(gate)[0]
        assert isinstance(dec_gate, gates.Gate)
        assert dec_gate.name == test_dec_gate.name
        assert dec_gate.parameters == test_dec_gate.parameters


def test_translate_gates(test_gates: list[gates.Gate]):
    """Test that translate gates outputs a list of gates as expected

    Args:
        test_gates (gates.Gate): list of gates to be translated
        decomposed_gates (list[gates.Gate]) : corresponding decomposition for test_gates
    """

    tr_gates = translate_gates(test_gates)
    # decomposed gates from fixture should look like this
    decomposed_gates = [
        Drag(0, np.pi, 0),
        Drag(1, np.pi / 2, -np.pi / 2),
        gates.RZ(1, np.pi),
        gates.CZ(0, 1),
        Drag(1, np.pi / 2, -np.pi / 2),
        gates.RZ(1, np.pi),
        Drag(0, 2.5, np.pi / 2),
    ]

    assert isinstance(tr_gates, list)
    for gate, dec_gate in zip(tr_gates, decomposed_gates):
        assert isinstance(gate, gates.Gate)
        assert gate.name == dec_gate.name
        assert gate.parameters == dec_gate.parameters


def test_native_gates():
    """Test native gates output is the intended set of gates"""

    # because of qibo things we have to initizlize the gate first
    # otherwise the return is a class, not an object
    nat_gates = native_gates()

    # test Drag
    drag = nat_gates[0](0, 0, 0)
    assert isinstance(drag, Drag)
    # test CZ
    cz = nat_gates[1](0, 1)
    assert isinstance(cz, gates.Gate)
