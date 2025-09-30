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
    Adjoint,
    H,
    BasicGate
)
from qililab.digital.circuit_transpiler_passes.numeric_helpers import _wrap_angle
from qilisdk.digital.exceptions import GateHasNoMatrixError
from qililab.digital.circuit_transpiler_passes.circuit_to_canonical_basis_pass import (
    CircuitToCanonicalBasisPass, 
    _H_as_U3,
    _CNOT_as_CZ_plus_1q,
    _CRZ_using_CNOT,
    _CRX_using_CRZ,
    _CRY_using_CRZ,
    _CU3_using_CNOT,
    _invert_basis_gate,
    _as_basis_1q,
    _sqrt_1q_gate_as_basis,
    _adjoint_1q,
)

import pytest
from unittest.mock import Mock
import numpy as np



def assert_equal_gate(list1: list[Gate], list2: list[Gate], abs=1e-15):
    assert len(list1) == len(list2)
    for i, j in zip(list1, list2):
        assert i.qubits == j.qubits
        assert i.name == j.name
        try:
            assert i.matrix == pytest.approx(j.matrix, abs=abs)
        except GateHasNoMatrixError:
            pass

class TestCircuitToCanonicalBasisPass:
    """Tests for the methods contained in circuit_to_canonical_basis_pass.py"""
    def test_gate_decompositions(self):
        try:
            _CNOT_as_CZ_plus_1q(0, 0)
            pytest.fail("Creating a controled gate were target and control qubit are the same shouldn't be possible")
        except ValueError:
            assert_equal_gate(_H_as_U3(2), [U3(2, theta=np.pi/2.0, phi=0.0, gamma=np.pi)])

            assert_equal_gate(_CNOT_as_CZ_plus_1q(1, 2), [*_H_as_U3(2), CZ(1, 2), *_H_as_U3(2)])

            for theta, phi, lam in zip((2*np.pi*np.random.random(20)-np.pi), 
                                       (2*np.pi*np.random.random(20)-np.pi), 
                                       (2*np.pi*np.random.random(20)-np.pi)):     
                assert_equal_gate(_CRZ_using_CNOT(1, 2, lam=lam), [RZ(2, phi=lam /2),
                                                                *_CNOT_as_CZ_plus_1q(1, 2),
                                                                RZ(2, phi=-lam/2),
                                                                *_CNOT_as_CZ_plus_1q(1, 2),])

                assert_equal_gate(_CU3_using_CNOT(1, 2, theta=theta, phi=phi, lam=lam), 
                                    [RZ(1, phi=_wrap_angle((lam + phi) / 2.0)),
                                    U3(2, theta=theta / 2.0, phi=phi, gamma=0.0),
                                    *_CNOT_as_CZ_plus_1q(1, 2),
                                    U3(2, theta=-theta / 2.0, phi=0.0, gamma=_wrap_angle(-(lam + phi) / 2.0)),
                                    *_CNOT_as_CZ_plus_1q(1, 2),
                                    RZ(2, phi=_wrap_angle((lam - phi) / 2.0))])
                
                assert_equal_gate(_CRX_using_CRZ(1, 2, theta=theta), [RY(2, theta=-np.pi / 2.0), *_CRZ_using_CNOT(1, 2, theta), RY(2, theta=np.pi / 2.0)])
                assert_equal_gate(_CRY_using_CRZ(1, 2, theta=theta), [RX(2, theta=np.pi / 2.0), *_CRZ_using_CNOT(1, 2, theta), RX(2, theta=-np.pi / 2.0)])

    def test_invert_basis_gate(self):
        test_set = [U3(0,theta=1,phi=2,gamma=3), X(0), RX(0,theta=2), Y(0), RY(0,theta=2), Z(0), RZ(0,phi=2), CZ(0,1), H(0), M(0), Exponential(X(0))]
        result_set = [U3(0,theta=-1,phi=-3,gamma=-2), RX(0,theta=-np.pi), RX(0,theta=-2), RY(0,theta=-np.pi), RY(0,theta=-2), RZ(0,phi=-np.pi),
                       RZ(0,phi=-2), CZ(0,1), U3(0, theta=-np.pi/2.0, phi=-np.pi, gamma=0.0), M(0), Adjoint(Exponential(X(0)))]
        result = []
        for gate in test_set:
            result += _invert_basis_gate(gate)
        assert_equal_gate(result, result_set)
    
    def test_as_basis_1q(self):
        basic_gate = Mock(BasicGate)
        basic_gate.nqubits = 1
        basic_gate.qubits = [0]
        basic_gate.matrix = np.array([[np.cos(0.5), -np.sin(0.5) * np.exp(1j*3)],
                                    [np.sin(0.5) * np.exp(1j*2), np.cos(0.5) * np.exp(1j*(2+3))]], dtype=complex)
        test_set = [U3(0,theta=1,phi=2,gamma=3), U1(0,phi=2), U2(0,phi=2,gamma=3), X(0), Y(0), 
                    Z(0), H(0), basic_gate]
        result_set = [U3(0,theta=1,phi=2,gamma=3), RZ(0,phi=2), U3(0,theta=np.pi/2,phi=2,gamma=3), RX(0, theta=np.pi), RY(0,theta=np.pi), 
                      RZ(0,phi=np.pi), U3(0, theta=np.pi/2.0, phi=0.0, gamma=np.pi), U3(0, theta=1, phi=2, gamma=3)]
        result = []
        for gate in test_set:
            result.append(_as_basis_1q(gate))
        assert_equal_gate(result, result_set)

        try:
            _as_basis_1q(Exponential(X(0)))
            pytest.fail("Not supported, should raise an error")
        except NotImplementedError:
            pass