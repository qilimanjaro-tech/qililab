import math
import pytest
import numpy as np
from qililab.digital.circuit_transpiler_passes.numeric_helpers import (
    _wrap_angle, 
    _round_f, 
    _is_close_mod_2pi, 
    _mat_RY, 
    _mat_RX,
    _mat_RZ,
    _mat_U3,
    _zyz_from_unitary,
    _unitary_sqrt_2x2,
    _EPS, 
    _SIG_DECIMALS)

_NUM_RANDOM = 30
_PI = math.pi

class TestNumericHelpers:
    def test_wrap_angle(self):
        angles = (angle*scalar for angle, scalar in zip(np.random.random(_NUM_RANDOM)*2*_PI - _PI, np.random.random(_NUM_RANDOM)*20-10))
        test_set = [0, -_PI, *angles]
        test_expected =  [0, -_PI, *((angle + _PI) % (2.0 * _PI) - _PI for angle in angles)]
        for set, expected in zip(test_set, test_expected):
            assert _wrap_angle(set) == (pytest.approx(expected, abs=10**-_SIG_DECIMALS)\
                                        if expected != -_PI else _PI)

    def test_round_f(self):
        for num, round_dec in zip((num * 10 ** -order for num, order in zip(np.random.random(_NUM_RANDOM), np.random.random(_NUM_RANDOM)*21 -1)),
                              (int(round_dec) for round_dec in np.random.random(_NUM_RANDOM)*15)):
            assert _round_f(num, round_dec) == (round(num, round_dec) if num >= 1e-16 else 0.0)

    def test_is_close_mod_2pi(self):
        test_a_set = [2, 0, 0, 1, 1]
        test_b_set = [3, _EPS, _EPS*0.999, 1+_PI, 1+2*_PI]
        expected_set = [False, False, True, False, True]
        for a, b, expected in zip(test_a_set, test_b_set, expected_set):
            assert _is_close_mod_2pi(a, b) == expected

    def test_mat_RZ(self):
        test_set = [0, *(2*_PI*np.random.random(_NUM_RANDOM)-_PI)]
        for phi in test_set:
            matrix = np.array([[np.exp(-1j*phi/2), 0.0],
                               [0.0, np.exp(1j*phi/2)]], dtype=complex)
            assert (_mat_RZ(phi) == matrix).all()

    def test_mat_RY(self):
        test_set = [0, *(2*_PI*np.random.random(_NUM_RANDOM)-_PI)]
        for theta in test_set:
            matrix = np.array([[math.cos(theta/2), -math.sin(theta/2)],
                               [math.sin(theta/2), math.cos(theta/2)]], dtype=complex)
            assert (_mat_RY(theta) == matrix).all()

    def test_mat_RX(self):
        test_set = [0, *(2*_PI*np.random.random(_NUM_RANDOM)-_PI)]
        for theta in test_set:
            matrix = np.array([[math.cos(theta/2), -1j*math.sin(theta/2)],
                               [-1j*math.sin(theta/2), math.cos(theta/2)]], dtype=complex)
            assert (_mat_RX(theta) == matrix).all()

    def test_mat_U3(self):
        for theta, phi, lam in zip((2*_PI*np.random.random(_NUM_RANDOM)-_PI), 
                                   (2*_PI*np.random.random(_NUM_RANDOM)-_PI), 
                                   (2*_PI*np.random.random(_NUM_RANDOM)-_PI)):
            matrix = np.array([[np.cos(theta/2)                   , -np.sin(theta/2) * np.exp(1j*lam)],
                               [np.sin(theta/2) * np.exp(1j*lam)  , np.cos(theta/2) * np.exp(1j*(phi+lam))]], dtype=complex)
            assert (_mat_U3(theta,phi,lam) == pytest.approx(matrix,8))

    def test_zyz_from_unitary(self):
        for theta, phi, lam in zip((2*_PI*np.random.random(_NUM_RANDOM)-_PI), 
                                   (2*_PI*np.random.random(_NUM_RANDOM)-_PI), 
                                   (2*_PI*np.random.random(_NUM_RANDOM)-_PI)):
            matrix1 = np.array([[np.cos(theta/2)                   , -np.sin(theta/2) * np.exp(1j*lam)],
                                [np.sin(theta/2) * np.exp(1j*phi)  , np.cos(theta/2) * np.exp(1j*(phi+lam))]], dtype=complex)
            matrix2 = np.array([[1, 0],
                                [0, np.exp(1j*(phi+lam))]], dtype=complex)
            theta2, phi2, lam2 = _zyz_from_unitary(matrix1)
            assert (((theta2, phi2, lam2) == pytest.approx((theta,phi,lam),abs=1e-8))\
                    or ((-theta2, _wrap_angle(phi2+_PI), _wrap_angle(lam2+_PI)) == pytest.approx((theta,phi,lam),abs=1e-8)))
            assert (_zyz_from_unitary(matrix2) == pytest.approx((0.0,0.0,_wrap_angle(phi+lam)),abs=1e-8))

    def test_unitary_sqrt_2x2(self):
        for theta, phi, lam, gamma in zip((2*_PI*np.random.random(10)-_PI), 
                                          (2*_PI*np.random.random(10)-_PI), 
                                          (2*_PI*np.random.random(10)-_PI),
                                          (2*_PI*np.random.random(10)-_PI)):
            matrix = _mat_RZ(phi) @ _mat_RY(theta) @ _mat_RZ(lam) * np.exp(0.5j * (gamma), dtype=complex)
            sqrt_matrix = _unitary_sqrt_2x2(matrix)
            assert sqrt_matrix @ sqrt_matrix == pytest.approx(matrix, abs=1e-15)
