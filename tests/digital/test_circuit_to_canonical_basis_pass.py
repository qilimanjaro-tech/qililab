from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    X,
    Y,
    Z,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Gate,
    M,
    Exponential,
    Controlled,
    Adjoint,
    H,
    BasicGate,
    I,
    S,
    T,
    CNOT,
)
from qililab.digital.circuit_transpiler_passes.numeric_helpers import _zyz_from_unitary, _unitary_sqrt_2x2
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass import CircuitToCanonicalBasisPass

import pytest
from unittest.mock import Mock, PropertyMock
import numpy as np



def assert_equal_gate(list1: list[Gate], list2: list[Gate], abs=1e-15):
    assert len(list1) == len(list2)
    for i, j in zip(list1, list2):
        assert i.name == j.name
        assert i.qubits == j.qubits
        try:
            assert i.matrix == pytest.approx(j.matrix, abs=abs)
        except GateHasNoMatrixError:
            pass

test_cases = [M(0), I(0), X(2), Y(0), Z(2), H(2), S(0), T(1), RX(1, theta=1), RY(2, theta=1), RZ(0, phi=2),
                U1(0, phi=2), U2(1, phi=2, gamma=3), U3(2, theta=1, phi=2, gamma=3),
                CZ(0,2), CNOT(2,1), SWAP(0,1)]
result_cases = [[M(0)], [], [RX(2, theta=np.pi)], [RY(0, theta=np.pi)], [RZ(2, phi=np.pi)], [U3(2, theta=np.pi/2, phi=0.0, gamma=np.pi)], [RZ(0, phi=np.pi/2)], [RZ(1, phi=np.pi/4)],
                [RX(1, theta=1)],[RY(2, theta=1)], [RZ(0, phi=2)], [RZ(0, phi=2)], [U3(1, theta=np.pi/2, phi=2, gamma=3)], [U3(2, theta=1, phi=2, gamma=3)], [CZ(0,2)],
                [U3(1, theta=np.pi/2, phi=0.0, gamma=np.pi), CZ(2, 1), U3(1, theta=np.pi/2, phi=0.0, gamma=np.pi)], 
                [U3(1, theta=np.pi/2, phi=0.0, gamma=np.pi), CZ(0,1), U3(1, theta=np.pi/2, phi=0.0, gamma=np.pi), 
                 U3(0, theta=np.pi/2, phi=0.0, gamma=np.pi), CZ(1,0), U3(0, theta=np.pi/2, phi=0.0, gamma=np.pi), 
                 U3(1, theta=np.pi/2, phi=0.0, gamma=np.pi), CZ(0,1), U3(1, theta=np.pi/2, phi=0.0, gamma=np.pi)]]
adjointed_cases = [[], [], [RX(2, theta=-np.pi)], [RY(0, theta=-np.pi)], [RZ(2, phi=-np.pi)], [U3(2, theta=-np.pi/2, phi=-np.pi, gamma=0.0)], [RZ(0, phi=-np.pi/2)], [RZ(1, phi=-np.pi/4)],
                    [RX(1, theta=-1)],[RY(2, theta=-1)], [RZ(0, phi=-2)], [RZ(0, phi=-2)], [U3(1, theta=-np.pi/2, phi=-3, gamma=-2)], [U3(2, theta=-1, phi=-3, gamma=-2)], [CZ(0,2)],
                    [U3(1, theta=-np.pi/2, phi=-np.pi, gamma=0.0), CZ(2, 1), U3(1, theta=-np.pi/2, phi=-np.pi, gamma=0.0)], 
                    [U3(1, theta=-np.pi/2, phi=-np.pi, gamma=0.0), CZ(0,1), U3(1, theta=-np.pi/2, phi=-np.pi, gamma=0.0), 
                    U3(0, theta=-np.pi/2, phi=-np.pi, gamma=0.0), CZ(1,0), U3(0, theta=-np.pi/2, phi=-np.pi, gamma=0.0), 
                    U3(1, theta=-np.pi/2, phi=-np.pi, gamma=0.0), CZ(0,1), U3(1, theta=-np.pi/2, phi=-np.pi, gamma=0.0)]]
class TestCircuitToCanonicalBasisPass:
    """Tests for the methods contained in circuit_to_canonical_basis_pass.py"""
    def test_gate_decompositions(self):
        result = []
        for i in range(len(test_cases)):
            result += result_cases[i]
        c = Circuit(3)
        c._gates = test_cases
        assert_equal_gate(CircuitToCanonicalBasisPass().run(c)._gates, result)

    def test_adjointed_gate_decompositions(self):
        result = []
        gates = []
        for i in range(1,len(test_cases)):
            result += adjointed_cases[i]
            gates += [Adjoint(test_cases[i])]
        c = Circuit(3)
        c._gates = gates
        assert_equal_gate(CircuitToCanonicalBasisPass().run(c)._gates, result)

    def test_controled_gate_decomposition(self):
        controled_gates = [Controlled(0, basic_gate=RX(2, theta=1)), Controlled(0, basic_gate=RY(2, theta=1)), 
                            Controlled(0, basic_gate=RZ(2, phi=1)), Controlled(0, basic_gate=U3(2, theta=1, phi=2, gamma=3)),
                            Controlled(0, basic_gate=S(2))]
        single_controled_results = [RX(2, theta=0.5), CZ(0, 2), RX(2, theta=-0.5), CZ(0, 2),
                                    RY(2, theta=0.5), CZ(0, 2), RY(2, theta=-0.5), CZ(0, 2),
                                    RZ(2, phi=0.5), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                        RX(2, theta=-0.5), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                    RZ(2, phi=0.5), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                        U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), U3(2, theta=-0.5, phi=0.0, gamma=-2.5), 
                                        U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                        U3(2, theta=0.5, phi=2, gamma=0.0),
                                    RZ(2, phi=np.pi/4), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                        RX(2, theta=-np.pi/4), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi)
                                     ]
        c = Circuit(3)
        c._gates = controled_gates
        assert_equal_gate(CircuitToCanonicalBasisPass().run(c)._gates, single_controled_results)

        multicontroled_gates = [Controlled(0,1, basic_gate=RX(2, theta=1)), Controlled(0,1, basic_gate=U1(2, phi=1))]
        multicontroled_results = [RX(2, theta=0.25), CZ(0, 2), RX(2, theta=-0.25), CZ(0, 2),
                                    U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                    RX(2, theta=-0.25), CZ(0, 2), RX(2, theta=0.25), CZ(0, 2),
                                    U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                    RX(2, theta=0.25), CZ(0, 2), RX(2, theta=-0.25), CZ(0, 2),
                                  RZ(2, phi=0.25), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                        RX(2, theta=-0.25), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                    U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                    RZ(2, phi=-0.25), U3(2, theta=-np.pi / 2, phi=-np.pi, gamma=0.0), CZ(0, 2), 
                                        RX(2, theta=0.25), CZ(0, 2), U3(2, theta=-np.pi / 2, phi=-np.pi, gamma=0.0),
                                    U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                    RZ(2, phi=0.25), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                        RX(2, theta=-0.25), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi)
                                    ]
        c = Circuit(3)
        c._gates = multicontroled_gates
        assert_equal_gate(CircuitToCanonicalBasisPass().run(c)._gates, multicontroled_results)

    def test_adjointed_and_controled(self):
        ad_cn_gates = [Adjoint(Controlled(0,1,basic_gate=(S(2)))), Controlled(0,1,basic_gate=Adjoint(Y(2)))]
        ad_cn_res_S = reversed([RZ(2, phi=-np.pi/8), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                    RX(2, theta=np.pi/8), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                RZ(2, phi=np.pi/8), U3(2, theta=-np.pi / 2, phi=-np.pi, gamma=0.0), CZ(0, 2), 
                                    RX(2, theta=-np.pi/8), CZ(0, 2), U3(2, theta=-np.pi / 2, phi=-np.pi, gamma=0.0),
                                U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                                RZ(2, phi=-np.pi/8), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(0, 2), 
                                    RX(2, theta=np.pi/8), CZ(0, 2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi)])
        ad_cn_res_Y = [RY(2, theta=-np.pi/4), CZ(0, 2), RY(2, theta=np.pi/4), CZ(0, 2),
                       U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                       RY(2, theta=np.pi/4), CZ(0, 2), RY(2, theta=-np.pi/4), CZ(0, 2),
                       U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi), CZ(1,2), U3(2, theta=np.pi / 2, phi=0.0, gamma=np.pi),
                       RY(2, theta=-np.pi/4), CZ(0, 2), RY(2, theta=np.pi/4), CZ(0, 2),]
        ad_cn_results = [*ad_cn_res_S, *ad_cn_res_Y]
        c = Circuit(3)
        c._gates = ad_cn_gates
        assert_equal_gate(CircuitToCanonicalBasisPass().run(c)._gates, ad_cn_results)

    def test_sqrt_1q_gate_as_basis(self):
        gates = [X(2), Y(0), Z(2), S(0), T(1), RX(1, theta=1), RY(2, theta=1), RZ(0, phi=2), U1(0, phi=2)]
        result_gates = [RX(2, theta=np.pi/2), RY(0, theta=np.pi/2), RZ(2, phi=np.pi/2), RZ(0, phi=np.pi/4), RZ(1, phi=np.pi/8),
                RX(1, theta=0.5),RY(2, theta=0.5), RZ(0, phi=1), RZ(0, phi=1)]
        for i in range(len(gates)):
            assert_equal_gate([CircuitToCanonicalBasisPass()._sqrt_1q_gate_as_basis(gates[i])], [result_gates[i]])
        
        U3gates = [H(0), U2(1, phi=2, gamma=3), U3(2, theta=1, phi=2, gamma=3)]
        result_U3_gates = [U3(0, theta=np.pi / 2, phi=0.0, gamma=np.pi), U3(0, theta=np.pi/2, phi=2, gamma=3), U3(0, theta=1, phi=2, gamma=3)]
        for i in range(len(U3gates)):
            Vs = _unitary_sqrt_2x2(result_U3_gates[i].matrix)
            th, ph, lam = _zyz_from_unitary(Vs)
            g = U3(U3gates[i].qubits[0], theta=th, phi=ph, gamma=lam)
            assert_equal_gate([CircuitToCanonicalBasisPass()._sqrt_1q_gate_as_basis(U3gates[i])], [g])

    def test_errors(self):
        c=Circuit(3)
        mock_Gate = Mock(Gate)
        mock_BasicGate_no_matrix = Mock(BasicGate)
        type(mock_BasicGate_no_matrix).matrix = PropertyMock(side_effect=GateHasNoMatrixError)
        try:
            c._gates = [Controlled(2,basic_gate=SWAP(0,1))]
            CircuitToCanonicalBasisPass().run(c)
            pytest.fail("Trying to pass a controled SWAP should rise an error if it isn't supported")
        except NotImplementedError:
            assert True
        try:
            c._gates = [mock_Gate]
            CircuitToCanonicalBasisPass().run(c)
            pytest.fail("Unsupported gates should raise an error")
        except NotImplementedError:
            assert True
        try:
            c._gates = [mock_BasicGate_no_matrix]
            CircuitToCanonicalBasisPass().run(c)
            pytest.fail("Unsupported gates should raise an error")
        except NotImplementedError:
            assert True
            
