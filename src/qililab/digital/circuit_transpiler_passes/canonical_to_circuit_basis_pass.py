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

from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np
from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CNOT,
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U1,
    U2,
    U3,
    Adjoint,
    BasicGate,
    Controlled,
    Exponential,
    Gate,
    H,
    I,
    M,
    X,
    Y,
    Z,
)

from .circuit_transpiler_pass import CircuitTranspilerPass

_EPS = 1e-10

# -------------------- numeric helpers --------------------


def _wrap_angle(a: float) -> float:
    a = (a + math.pi) % (2.0 * math.pi) - math.pi
    if abs(a + math.pi) < 1e-15:
        return math.pi
    return a


def _is_close_mod_2pi(a: float, b: float, eps: float = 1e-9) -> bool:
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
    return _mat_RZ(phi) @ _mat_RY(theta) @ _mat_RZ(lam)


def _zyz_from_unitary(U: np.ndarray) -> Tuple[float, float, float]:
    if U.shape != (2, 2):
        raise ValueError("Expected 2x2 unitary for ZYZ decomposition.")
    det = np.linalg.det(U)
    if abs(det) < _EPS:
        raise ValueError("Matrix is singular.")
    U = U * np.exp(-0.5j * np.angle(det))  # remove global phase

    a00, a01 = U[0, 0], U[0, 1]
    a10, a11 = U[1, 0], U[1, 1]

    c = np.clip(abs(a00), 0.0, 1.0)
    theta = 2.0 * math.acos(c)
    s = math.sin(theta / 2.0)

    if s < 1e-12:
        phi = 0.0
        lam = _wrap_angle(-2.0 * np.angle(a00))
        return (0.0, phi, lam)

    phi = _wrap_angle(np.angle(a10) - np.angle(a00))
    lam = _wrap_angle(np.angle(a01) - np.angle(a11))
    return (theta, phi, lam)


def _unitary_sqrt_2x2(U: np.ndarray) -> np.ndarray:
    """Principal square root of a 2x2 unitary via eigendecomp (robust for 1-qubit)."""
    w, V = np.linalg.eig(U)
    # project eigenvalues to unit circle to fight tiny drift
    ph = np.angle(w)
    sqrt_w = np.exp(0.5j * ph)
    return V @ np.diag(sqrt_w) @ np.linalg.inv(V)


# -------------------- basis building blocks --------------------


def _H_as_U3(q: int) -> List[Gate]:
    # H = U2(0, π) = U3(π/2, 0, π) up to global phase
    return [U3(q, theta=math.pi / 2.0, phi=0.0, gamma=math.pi)]


def _CNOT_as_CZ_plus_1q(c: int, t: int) -> List[Gate]:
    # CNOT = (I ⊗ H) · CZ · (I ⊗ H)
    return [*_H_as_U3(t), CZ(c, t), *_H_as_U3(t)]


def _CRZ_using_CNOT(c: int, t: int, lam: float) -> List[Gate]:
    # CRZ(λ) = (I⊗RZ(λ/2)) · CNOT · (I⊗RZ(-λ/2)) · CNOT
    return [
        RZ(t, phi=_wrap_angle(lam / 2.0)),
        *_CNOT_as_CZ_plus_1q(c, t),
        RZ(t, phi=_wrap_angle(-lam / 2.0)),
        *_CNOT_as_CZ_plus_1q(c, t),
    ]


def _CRX_using_CRZ(c: int, t: int, theta: float) -> List[Gate]:
    # RX(θ) = RY(-π/2) · RZ(θ) · RY(π/2)
    return [
        RY(t, theta=-math.pi / 2.0),
        *_CRZ_using_CNOT(c, t, theta),
        RY(t, theta=math.pi / 2.0),
    ]


def _CRY_using_CRZ(c: int, t: int, theta: float) -> List[Gate]:
    # RY(θ) = RX(π/2) · RZ(θ) · RX(-π/2)
    return [
        RX(t, theta=math.pi / 2.0),
        *_CRZ_using_CNOT(c, t, theta),
        RX(t, theta=-math.pi / 2.0),
    ]


def _CU3_using_CNOT(c: int, t: int, theta: float, phi: float, lam: float) -> List[Gate]:
    # Two-CX synthesis (with CX realized by H-CZ-H)
    return [
        RZ(c, phi=_wrap_angle((lam + phi) / 2.0)),
        U3(t, theta=theta / 2.0, phi=phi, gamma=0.0),
        *_CNOT_as_CZ_plus_1q(c, t),
        U3(t, theta=-theta / 2.0, phi=0.0, gamma=_wrap_angle(-(lam + phi) / 2.0)),
        *_CNOT_as_CZ_plus_1q(c, t),
        RZ(t, phi=_wrap_angle((lam - phi) / 2.0)),
    ]


def _invert_basis_gate(g: Gate) -> List[Gate]:
    if isinstance(g, U3):
        return [U3(g.qubits[0], theta=-g.theta, phi=-g.gamma, gamma=-g.phi)]
    if isinstance(g, RX):
        return [RX(g.qubits[0], theta=-g.theta)]
    if isinstance(g, RY):
        return [RY(g.qubits[0], theta=-g.theta)]
    if isinstance(g, RZ):
        return [RZ(g.qubits[0], phi=-g.phi)]
    if isinstance(g, CZ):
        return [CZ(g.control_qubits[0], g.target_qubits[0])]
    if isinstance(g, M):
        return [g]
    if isinstance(g, H):
        return _H_as_U3(g.qubits[0])[::-1]
    if isinstance(g, X):
        return [RX(g.qubits[0], theta=-math.pi)]
    if isinstance(g, Y):
        return [RY(g.qubits[0], theta=-math.pi)]
    if isinstance(g, Z):
        return [RZ(g.qubits[0], phi=-math.pi)]
    return [Adjoint(g)]  # type: ignore[type-var]


# -------------------- NEW: multi-control support --------------------


def _as_basis_1q(g: Gate) -> Gate:
    """Return an equivalent 1-qubit gate expressed as U3/RX/RY/RZ."""
    q = g.qubits[0]
    if isinstance(g, (RX, RY, RZ, U3)):
        return g
    if isinstance(g, U1):
        return RZ(q, phi=g.phi)
    if isinstance(g, U2):
        return U3(q, theta=math.pi / 2.0, phi=g.phi, gamma=g.gamma)
    if isinstance(g, H):
        return _H_as_U3(q)[0]
    if isinstance(g, X):
        return RX(q, theta=math.pi)
    if isinstance(g, Y):
        return RY(q, theta=math.pi)
    if isinstance(g, Z):
        return RZ(q, phi=math.pi)
    if isinstance(g, BasicGate) and g.nqubits == 1:
        # generic 1q: derive U3 angles from its matrix
        th, ph, lam = _zyz_from_unitary(g.matrix)
        return U3(q, theta=th, phi=ph, gamma=lam)
    raise NotImplementedError(f"Unsupported 1-qubit gate type {type(g).__name__} in _as_basis_1q")


def _sqrt_1q_gate_as_basis(g: Gate) -> Gate:
    """Return V such that V^2 = g, as a basis gate (U3/RX/RY/RZ)."""
    q = g.qubits[0]
    # Fast paths (avoid numerics)
    if isinstance(g, RZ):
        return RZ(q, phi=g.phi / 2.0)
    if isinstance(g, RX):
        return RX(q, theta=g.theta / 2.0)
    if isinstance(g, RY):
        return RY(q, theta=g.theta / 2.0)
    if isinstance(g, Z):
        return RZ(q, phi=math.pi / 2.0)
    if isinstance(g, X):
        return RX(q, theta=math.pi / 2.0)
    if isinstance(g, Y):
        return RY(q, theta=math.pi / 2.0)
    if isinstance(g, U1):
        return RZ(q, phi=g.phi / 2.0)

    # General 1q unitary (U2/U3/generic): use eigen-decomposition
    if isinstance(g, U2):
        U = _mat_U3(math.pi / 2.0, g.phi, g.gamma)
    elif isinstance(g, U3):
        U = _mat_U3(g.theta, g.phi, g.gamma)
    elif isinstance(g, BasicGate) and g.nqubits == 1:
        U = g.matrix
    else:
        # Map to basis first, then recurse
        return _sqrt_1q_gate_as_basis(_as_basis_1q(g))

    Vs = _unitary_sqrt_2x2(U)
    th, ph, lam = _zyz_from_unitary(Vs)
    return U3(q, theta=th, phi=ph, gamma=lam)


def _adjoint_1q(g: Gate) -> Gate:
    q = g.qubits[0]
    if isinstance(g, RX):
        return RX(q, theta=-g.theta)
    if isinstance(g, RY):
        return RY(q, theta=-g.theta)
    if isinstance(g, RZ):
        return RZ(q, phi=-g.phi)
    if isinstance(g, U3):
        return U3(q, theta=-g.theta, phi=-g.gamma, gamma=-g.phi)
    # Map and retry
    return _adjoint_1q(_as_basis_1q(g))


def _single_controlled(c: int, target_gate: Gate) -> List[Gate]:
    """Decompose a single-controlled 1-qubit gate with control c to basis."""
    t = target_gate.qubits[0]
    if isinstance(target_gate, RZ):
        return _CRZ_using_CNOT(c, t, target_gate.phi)
    if isinstance(target_gate, RX):
        return _CRX_using_CRZ(c, t, target_gate.theta)
    if isinstance(target_gate, RY):
        return _CRY_using_CRZ(c, t, target_gate.theta)
    if isinstance(target_gate, U3):
        return _CU3_using_CNOT(c, t, target_gate.theta, target_gate.phi, target_gate.gamma)
    # Map and retry
    return _single_controlled(c, _as_basis_1q(target_gate))


def _multi_controlled(controls: List[int], base_1q: Gate) -> List[Gate]:
    """
    Ancilla-free recursive synthesis of C^k(base_1q) using
    C^{k-1}(V), CNOT, C^{k-1}(V†), CNOT, C^{k-1}(V) with V^2 = base_1q.
    Emits only CZ + {U3,RX,RY,RZ}.
    """
    # assert base_1q.nqubits == 1
    if not controls:
        # no control: just the base gate
        return [base_1q]
    if len(controls) == 1:
        return _single_controlled(controls[0], base_1q)

    # reduce one control
    c_last = controls[-1]
    rest = controls[:-1]

    V = _sqrt_1q_gate_as_basis(base_1q)
    Vd = _adjoint_1q(V)

    t = base_1q.qubits[0]
    seq: List[Gate] = []
    seq += _multi_controlled(rest, V)
    seq += _CNOT_as_CZ_plus_1q(c_last, t)
    seq += _multi_controlled(rest, Vd)
    seq += _CNOT_as_CZ_plus_1q(c_last, t)
    seq += _multi_controlled(rest, V)
    return seq


# -------------------- The pass --------------------


class CanonicalToCircuitBasisPass(CircuitTranspilerPass):
    """
    Canonicalize to the circuit basis {U3, RX, RY, RZ, CZ} (+ M).
    """

    def __init__(self, *, fuse_1q: bool = True) -> None:
        self.fuse_1q = fuse_1q

    def run(self, circuit: Circuit) -> Circuit:
        # 1) Rewrite to basis (including multi-control expansion)
        seq = self._rewrite_list(circuit.gates)

        # 2) Optionally fuse adjacent 1Q gates per wire
        if self.fuse_1q:
            seq = self._fuse_1q_runs(seq)

        new_circuit = Circuit(circuit.nqubits)
        for g in seq:
            new_circuit.add(g)

        self.append_circuit_to_context(new_circuit)

        return new_circuit

    # ---------- rewriting ----------

    def _rewrite_list(self, gates: List[Gate]) -> List[Gate]:
        out: List[Gate] = []
        for g in gates:
            out += self._rewrite_gate(g)
        return out

    def _rewrite_gate(self, g: Gate) -> List[Gate]:
        # Measurements keep
        if isinstance(g, M):
            return [g]

        # Already basis
        if isinstance(g, (U3, RX, RY, RZ, CZ)):
            return [g]

        # Simple 1Q
        if isinstance(g, I):
            return []
        if isinstance(g, H):
            return _H_as_U3(g.qubits[0])
        if isinstance(g, X):
            return [RX(g.qubits[0], theta=math.pi)]
        if isinstance(g, Y):
            return [RY(g.qubits[0], theta=math.pi)]
        if isinstance(g, Z):
            return [RZ(g.qubits[0], phi=math.pi)]

        # Param 1Q
        if isinstance(g, U1):
            return [RZ(g.qubits[0], phi=g.phi)]
        if isinstance(g, U2):
            return [U3(g.qubits[0], theta=math.pi / 2.0, phi=g.phi, gamma=g.gamma)]

        # 2Q
        if isinstance(g, CZ):
            return [g]
        if isinstance(g, CNOT):
            c, t = g.control_qubits[0], g.target_qubits[0]
            return _CNOT_as_CZ_plus_1q(c, t)
        if isinstance(g, SWAP):
            a, b = g.target_qubits
            return _CNOT_as_CZ_plus_1q(a, b) + _CNOT_as_CZ_plus_1q(b, a) + _CNOT_as_CZ_plus_1q(a, b)

        # Controlled (arbitrary number of controls) over a 1-qubit target gate
        if isinstance(g, Controlled):
            ctrls = list(g.control_qubits)
            base = g.basic_gate
            if base.nqubits != 1:
                raise NotImplementedError("Controlled of multi-qubit gates not supported.")
            t = base.qubits[0]
            base1q = _as_basis_1q(base)
            # Ensure the mapped base gate acts on the same target
            if base1q.qubits[0] != t:
                # rebuild with same type on t
                if isinstance(base1q, U3):
                    base1q = U3(t, theta=base1q.theta, phi=base1q.phi, gamma=base1q.gamma)
                elif isinstance(base1q, RX):
                    base1q = RX(t, theta=base1q.theta)
                elif isinstance(base1q, RY):
                    base1q = RY(t, theta=base1q.theta)
                elif isinstance(base1q, RZ):
                    base1q = RZ(t, phi=base1q.phi)
            return _multi_controlled(ctrls, base1q)

        # Adjoint
        if isinstance(g, Adjoint):
            base_seq = self._rewrite_gate(g.basic_gate)
            inv: List[Gate] = []
            for x in reversed(base_seq):
                inv += _invert_basis_gate(x)
            return inv

        # Exponential(1q)
        if isinstance(g, Exponential):
            base = g.basic_gate
            if base.nqubits != 1:
                raise NotImplementedError("Exponential of multi-qubit gates not supported.")
            U = g.matrix
            th, ph, lam = _zyz_from_unitary(U)
            return [U3(base.qubits[0], theta=th, phi=ph, gamma=lam)]

        # Generic 1Q gate
        if isinstance(g, BasicGate) and g.nqubits == 1:
            th, ph, lam = _zyz_from_unitary(g.matrix)
            return [U3(g.qubits[0], theta=th, phi=ph, gamma=lam)]

        raise NotImplementedError(f"No canonicalization rule for {type(g).__name__}")

    # ---------- 1Q fusion ----------

    def _fuse_1q_runs(self, seq: List[Gate]) -> List[Gate]:
        out: List[Gate] = []
        pending: dict[int, np.ndarray] = {}

        def flush(q: int):
            if q not in pending:
                return
            U = pending.pop(q)
            th, ph, lam = _zyz_from_unitary(U)
            th, ph, lam = _wrap_angle(th), _wrap_angle(ph), _wrap_angle(lam)
            if abs(th) < 1e-9:
                out.append(RZ(q, phi=_wrap_angle(ph + lam)))
                return
            if _is_close_mod_2pi(ph, 0.0) and _is_close_mod_2pi(lam, 0.0):
                out.append(RY(q, theta=th))
                return
            if _is_close_mod_2pi(ph, -math.pi / 2.0) and _is_close_mod_2pi(lam, math.pi / 2.0):
                out.append(RX(q, theta=th))
                return
            out.append(U3(q, theta=th, phi=ph, gamma=lam))

        def apply(q: int, U: np.ndarray):
            pending[q] = U @ pending[q] if q in pending else U

        def flush_touches(qubits: Tuple[int, ...]):
            for q in qubits:
                flush(q)

        for g in seq:
            if isinstance(g, (U3, RX, RY, RZ)):
                q = g.qubits[0]
                if isinstance(g, U3):
                    U = _mat_U3(g.theta, g.phi, g.gamma)
                elif isinstance(g, RX):
                    U = _mat_RX(g.theta)
                elif isinstance(g, RY):
                    U = _mat_RY(g.theta)
                else:
                    U = _mat_RZ(g.phi)
                apply(q, U)
            elif isinstance(g, CZ):
                flush_touches((g.control_qubits[0], g.target_qubits[0]))
                out.append(g)
            elif isinstance(g, M):
                flush_touches(g.qubits)
                out.append(g)
            else:
                flush_touches(g.qubits)
                out.append(g)

        for q in list(pending.keys()):
            flush(q)

        return out
