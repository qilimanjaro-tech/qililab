import numpy as np
import pytest
from qibo import gates

from qililab.digital.gate_decompositions import GateDecompositions, native_gates, translate_gates
from qililab.digital.native_gates import Drag, Wait


@pytest.fixture(name="test_gates")
def get_gates() -> list[gates.Gate]:
    """Fixture that returns a set of gates for the test"""
    return [gates.X(0), gates.Align(0, 16), gates.CNOT(0, 1), gates.RY(0, 2.5)]


def test_gatedecompositions(test_gates: list[gates.Gate]):
    """Test that class GateDecompositions creates a dictionary of gate translations

    Args:
        test_gates (list[gates.Gate]): list of gates to be translated
    """
    decomp = GateDecompositions()
    # add some fake decompositions
    decomp.add(gates.RY, lambda gate: [gates.U3(0, gate.parameters[0], 2, 0)])
    decomp.add(gates.X, [gates.Y(0), gates.Z(0)])
    decomp.add(gates.CNOT, lambda gate: [gates.SWAP(0, 1)])
    decomp.add(gates.Align, lambda gate: [Wait(0, gate.parameters[0])])

    # decomposed gates from fixture should look like this
    decomposed_gates = [gates.Y(0), gates.Z(0), Wait(0, 16), gates.SWAP(0, 1), gates.U3(0, 2.5, 2, 0)]

    assert isinstance(decomp.decompositions, dict)

    # check that decomposed gates is the same as decomposed_gates
    new_gates = []
    for gate in test_gates:
        new_gates.extend(decomp(gate))
    for gate, dec_gate in zip(new_gates, decomposed_gates):
        assert isinstance(gate, gates.Gate)
        assert gate.name == dec_gate.name
        assert gate.parameters == dec_gate.parameters


def test_translate_gates(test_gates: list[gates.Gate]):
    """Test that translate gates outputs a list of gates as expected

    Args:
        test_gates (gates.Gate): list of gates to be translated
    """

    tr_gates = translate_gates(test_gates)
    # decomposed gates from fixture should look like this
    decomposed_gates = [
        Drag(0, np.pi, 0),
        Wait(0, 16),
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

    assert native_gates() == (Drag, gates.CZ, Wait)
