# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math

import numpy as np

# ======================= numeric helpers =======================

_EPS = 1e-10
_SIG_DECIMALS = 12


def _wrap_angle(a: float) -> float:
    a = (a + math.pi) % (2.0 * math.pi) - math.pi
    if abs(a + math.pi) < 1e-15:
        return math.pi
    return a


def _round_f(x: float, d: int = _SIG_DECIMALS) -> float:
    return 0.0 if abs(x) < 1e-16 else round(x, d)


def _is_close_mod_2pi(a: float, b: float, eps: float = _EPS) -> bool:
    return abs(_wrap_angle(a - b)) < eps


def _mat_RZ(phi: float) -> np.ndarray:
    return np.array([[np.exp(-0.5j * phi), 0.0], [0.0, np.exp(0.5j * phi)]], dtype=complex)


def _mat_RY(theta: float) -> np.ndarray:
    c, s = math.cos(theta / 2.0), math.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=complex)


def _mat_RX(theta: float) -> np.ndarray:
    c, s = math.cos(theta / 2.0), -1j * math.sin(theta / 2.0)
    return np.array([[c, s], [s, c]], dtype=complex)


def _mat_U3(theta: float, phi: float, lam: float) -> np.ndarray:
    # Convention: U3(θ, φ, λ) = RZ(φ) · RY(θ) · RZ(λ)
    return _mat_RZ(phi) @ _mat_RY(theta) @ _mat_RZ(lam) * np.exp(0.5j * (phi + lam), dtype=complex)


def _zyz_from_unitary(U: np.ndarray) -> tuple[float, float, float]:
    if U.shape != (2, 2):
        raise ValueError("Expected 2x2 unitary for ZYZ decomposition.")
    det = np.linalg.det(U)
    if abs(det) < _EPS:
        raise ValueError("Matrix is singular.")
    # remove phase to a U3 rotation
    phase = np.angle(U[0, 0])
    U = U / np.exp(1j * phase, dtype=complex)

    a00, a01 = U[0, 0], U[0, 1]
    a10, a11 = U[1, 0], U[1, 1]
    theta = 2.0 * math.atan2(np.abs(a01), np.abs(a00))
    s = math.sin(theta / 2.0)

    if s < 1e-12:
        lam = _wrap_angle(np.angle(a11))
        return (0.0, 0.0, lam)

    phi = _wrap_angle(np.angle(a10))
    lam = _wrap_angle(np.angle(-a01))
    return (theta, phi, lam)


def _unitary_sqrt_2x2(U: np.ndarray) -> np.ndarray:
    """Principal square root of a 2x2 unitary via eigendecomp (robust for 1-qubit)."""
    w, V = np.linalg.eig(U)
    ph = np.angle(w)
    sqrt_w = np.exp(0.5j * ph)
    return V @ np.diag(sqrt_w) @ np.linalg.inv(V)
