import math
import pytest
from unittest.mock import Mock

from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CZ,
    RX,
    RY,
    RZ,
    U3,
    Gate,
    M,
    Z
)

from qilisdk.digital.exceptions import GateHasNoMatrixError
from qililab.digital.native_gates import Drag

from qililab.digital.circuit_transpiler_passes.canonical_basis_to_native_set_pass import CanonicalBasisToNativeSetPass
from qililab.digital.circuit_transpiler_passes.numeric_helpers import _wrap_angle

def assert_equal_gate(list1: list[Gate], list2: list[Gate]):
    print(list1,f'\n', list2)
    assert len(list1) == len(list2)
    for i, j in zip(list1, list2):
        assert i.name == j.name
        assert i.qubits == j.qubits
        try:
            assert (i.matrix == j.matrix).all()
        except GateHasNoMatrixError:
            pass

class TestCanonicalBasisToNativeSetPass:
    def test_run(self):
        inp = Circuit(3)
        inp._gates = [RZ(0, phi=0.5),RX(0, theta=1), RZ(1, phi=0.5), RZ(0, phi=0.5), RY(1, theta=1), 
                      U3(0, theta=0.5, phi=1, gamma=1.5), RZ(2, phi=0.5), RZ(1, phi=0.5), RZ(1, phi=0.5), RZ(0, phi=0.5), CZ(1,2), M(0)]
        out_regular = [RZ(0, phi=0.5), Drag(0, theta=1, phase=0), RZ(1, phi=0.5), Drag(1, theta=1, phase=math.pi/2), RZ(0, phi=0.5), Drag(0, theta=0.5, phase=math.pi/2 + 1), 
                       RZ(1, phi=1), RZ(2, phi=0.5), CZ(1,2), M(0)]
        assert_equal_gate(CanonicalBasisToNativeSetPass().run(inp)._gates, out_regular)

        out_keep_virtual_rz = [Drag(0, theta=1, phase=0), Drag(1, theta=1, phase=math.pi/2), Drag(0, theta=0.5, phase=math.pi/2 + 1), CZ(1,2), M(0)]
        assert_equal_gate(CanonicalBasisToNativeSetPass(keep_virtual_rz=False).run(inp)._gates, out_keep_virtual_rz)

        out_merge_consecutive_rz = [RZ(0, phi=0.5), Drag(0, theta=1, phase=0), RZ(1, phi=0.5), RZ(0, phi=0.5), Drag(1, theta=1, phase=math.pi/2),
                                      Drag(0, theta=0.5, phase=math.pi/2 + 1), RZ(0, phi=2.5), RZ(2, phi=0.5), RZ(1, phi=0.5), RZ(1, phi=0.5), RZ(0, phi=0.5), CZ(1,2), M(0)]
        assert_equal_gate(CanonicalBasisToNativeSetPass(merge_consecutive_rz=False).run(inp)._gates, out_merge_consecutive_rz)

        out_drop_rz_before_measure = [RZ(0, phi=0.5), Drag(0, theta=1, phase=0), RZ(1, phi=0.5), Drag(1, theta=1, phase=math.pi/2), RZ(0, phi=0.5), 
                                      Drag(0, theta=0.5, phase=math.pi/2 + 1), RZ(1, phi=1), RZ(2, phi=0.5), CZ(1,2), RZ(0, phi=3), M(0)]
        assert_equal_gate(CanonicalBasisToNativeSetPass(drop_rz_before_measure=False).run(inp)._gates, out_drop_rz_before_measure)

    def test_edges(self):
        THE_circuit = Circuit(1)
        THE_circuit._gates = [M(0)]
        assert CanonicalBasisToNativeSetPass().run(THE_circuit) != THE_circuit

        non_canonical_gate = Circuit(1)
        non_canonical_gate._gates = [Z(0)]
        try:
            CanonicalBasisToNativeSetPass().run(non_canonical_gate)
            pytest.fail('Non-canonical gates should raise an error')
        except NotImplementedError:
            assert True

        empty = Circuit(1)
        assert CanonicalBasisToNativeSetPass().run(empty)._gates == []
        