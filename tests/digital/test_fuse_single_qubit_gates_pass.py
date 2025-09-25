from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U3,
    Gate,
    M,
)
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qililab.digital.circuit_transpiler_passes.fuse_single_qubit_gates_pass import FuseSingleQubitGatesPass
from qililab.digital.circuit_transpiler_passes.numeric_helpers import (
    _is_close_mod_2pi,
    _mat_RX,
    _mat_RY,
    _mat_RZ,
    _mat_U3,
    _wrap_angle,
    _zyz_from_unitary,
)
import pytest
import numpy as np

def assert_equal_gate(list1: list[Gate], list2: list[Gate]):
    assert len(list1) == len(list2)
    for i, j in zip(list1, list2):
        assert i.qubits == j.qubits
        assert i.name == j.name
        try:
            assert (i.matrix == j.matrix).all()
        except GateHasNoMatrixError:
            pass

class TestFuseSingleQubitGatesPass:
    def test_run(self):
        test_x = Circuit(1)
        test_x._gates = [RX(0, theta=2)]
        assert_equal_gate(FuseSingleQubitGatesPass().run(test_x)._gates, [RX(0,theta=2)])