import numpy as np
import pytest
from qilisdk.digital import (
    CNOT,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Circuit,
    Gate,
    H,
    I,
    X,
    Y,
    Z,
)
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qilisdk.digital.gates import Adjoint, Controlled, M
from qililab.digital.circuit_transpiler_passes.cancel_identity_pairs_pass import CancelIdentityPairsPass, _first_nonzero_phase, _EPS, _try_matrix

def assert_equal_gate(list1: list[Gate], list2: list[Gate]):
    assert len(list1) == len(list2)
    for i, j in zip(list1, list2):
        assert i.qubits == j.qubits
        assert i.name == j.name
        try:
            assert (i.matrix == j.matrix).all()
        except GateHasNoMatrixError:
            pass

class TestCancelIdentityPairsPass:
    def test_involutions_run(self):
        h_test = Circuit(2)
        h_test._gates = [CZ(0, 1), SWAP(0, 1), H(0), X(0), X(0), I(1), H(0), SWAP(1,0), CNOT(0, 1), CNOT(1, 0),CZ(0, 1)]
        assert_equal_gate(CancelIdentityPairsPass().run(h_test)._gates, 
                            [CZ(0, 1), CNOT(0, 1), CNOT(1, 0), CZ(0, 1)])

        rx_test = Circuit(2)
        rx_test._gates = [RX(0,theta=np.pi/2), RX(0,theta=-np.pi/2), RX(0,theta=np.pi/2), RX(0,theta=np.pi/2), RX(1,theta=-np.pi/2)]
        assert_equal_gate(CancelIdentityPairsPass().run(rx_test)._gates,  [RX(0,theta=np.pi/2), RX(0,theta=np.pi/2), RX(1,theta=-np.pi/2)])

        rot_test = Circuit(2)
        rot_test._gates = [RY(0,theta=np.pi/2), RY(0,theta=-np.pi/2), RZ(1,phi=0), RZ(1,phi=0),
                           U1(1,phi=np.pi/2), U1(1,phi=-np.pi/2)]
        assert_equal_gate(CancelIdentityPairsPass().run(rot_test)._gates,  [])

        u3_test = Circuit(2)
        u3_test._gates = [U3(1,theta=2,phi=3,gamma=4), U3(1,theta=-2,phi=-4,gamma=-3),
                          U3(1,theta=2,phi=3,gamma=4), U3(1,theta=-2,phi=4,gamma=-3)]
        assert_equal_gate(CancelIdentityPairsPass().run(u3_test)._gates,  [U3(1,theta=2,phi=3,gamma=4), U3(1,theta=-2,phi=4,gamma=-3)])

        u2_test = Circuit(2)
        u2_test._gates = [U2(0, phi=2, gamma=3), U3(0, theta=-np.pi/2 , phi=-3, gamma=-2), U2(0, phi=2, gamma=3), U3(0, theta=-np.pi/2 , phi=-2, gamma=-3), U2(1, phi=3, gamma=2)]
        assert_equal_gate(CancelIdentityPairsPass().run(u2_test)._gates,  [U2(0, phi=2, gamma=3), U3(0, theta=-np.pi/2 , phi=-2, gamma=-3), U2(1, phi=3, gamma=2)])

        ad_co_test = Circuit(2)
        ad_co_test._gates = [Adjoint(Y(1)),Adjoint(Y(1)), Adjoint(Y(1)),Adjoint(Y(0)),Adjoint(Z(0)),
                             Controlled(1,basic_gate=Y(0)),Controlled(1,basic_gate=Y(0)), 
                             Controlled(1,basic_gate=Y(0)), Controlled(0,basic_gate=Y(1)), Controlled(0,basic_gate=Z(1))]
        assert_equal_gate(CancelIdentityPairsPass().run(ad_co_test)._gates,  [Adjoint(Y(1)),Adjoint(Y(0)),Adjoint(Z(0)), 
                                                                              Controlled(1,basic_gate=Y(0)), Controlled(0,basic_gate=Y(1)), Controlled(0,basic_gate=Z(1))])


    def test_first_nonzero_phase(self):
        c_number1 = np.array([0 - 0j,0 + _EPS*1j])
        c_number2 = np.array([-1+1j])
        assert _first_nonzero_phase(c_number1) == 0.0
        assert _first_nonzero_phase(c_number2) == np.pi*3/4
    
    def test_try_matrix (self):
        gate1 = CZ(2,3)
        gate2 = M(2)
        assert (_try_matrix(gate1) == np.array([[[ 1.+0.j,  0.+0.j,  0.+0.j,  0.+0.j],
                                                [ 0.+0.j,  1.+0.j,  0.+0.j,  0.+0.j],
                                                [ 0.+0.j,  0.+0.j,  1.+0.j,  0.+0.j],
                                                [ 0.+0.j,  0.+0.j,  0.+0.j, -1.+0.j]]])).all()
        assert _try_matrix(gate2) == None

