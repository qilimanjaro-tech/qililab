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

import cmath
import math
from copy import deepcopy
from typing import Any, ClassVar

import numpy as np
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

from .circuit_transpiler_pass import CircuitTranspilerPass
from .numeric_helpers import _EPS, _round_f, _wrap_angle


def _first_nonzero_phase(U: np.ndarray) -> float:
    # phase of the first element with |.| > EPS
    for z in np.nditer(U, flags=["refs_ok"]):
        val = complex(z)  # type: ignore[call-overload]
        if abs(val) > _EPS:
            return cmath.phase(val)
    return 0.0


def _dephased_signature(U: np.ndarray) -> tuple[tuple[float, float], ...]:
    """Remove global phase and return a rounded (re, im) tuple signature."""
    if U.size == 0:
        return ()
    phi = _first_nonzero_phase(U)
    F = U * np.exp(-1j * phi)
    flat = F.reshape(-1)
    sig: list[tuple[float, float]] = []
    for z in flat:
        sig.append((_round_f(z.real), _round_f(z.imag)))
    return tuple(sig)


def _try_matrix(g: Gate) -> np.ndarray | None:
    try:
        return g.matrix
    except GateHasNoMatrixError:
        return None


# ------------------------ Canonical keys for matching ------------------------


class CancelIdentityPairsPass(CircuitTranspilerPass):
    """
    Cancel pairs of gates whose product is identity (up to global phase), across
    disjoint-qubit operations. Runs to a fixed point.

    It handles:
      • Involutions: H, X, Y, Z, CNOT, CZ, SWAP (gate; same gate cancels).
      • Parameter inverses: RX(θ)/RY(θ)/RZ(φ)/U1(φ) with negative angles;
        U3(θ,φ,λ) with U3(-θ, -λ, -φ).
      • Adjoint pairing: G with Adjoint(G).
      • Controlled^k: Controlled^k(U) with Controlled^k(U†), same controls/target.
      • Fallback: any two gates with matrix product ≈ identity (on the same qubits).

    Blocking:
      • Any operation that touches a qubit clears any pending candidate on that qubit.
      • Operations on disjoint qubits do not block.

    Notes:
      • `I` is dropped immediately.
      • For symmetric 2Q gates (CZ, SWAP) we normalize the qubit key to an unordered pair
        so CZ(a,b) cancels with CZ(b,a).
      • Measurements (M) are barriers on their qubits.
    """

    # Self-inverse (involution) gate classes we recognize cheaply
    _INVOLUTION_TYPES: ClassVar[tuple[type[Gate], ...]] = (H, X, Y, Z, CNOT, CZ, SWAP)

    def run(self, circuit: Circuit) -> Circuit:
        gates = list(circuit.gates)

        while True:
            stack: dict[tuple[Any, tuple[int, ...]], int] = {}
            to_delete: set[int] = set()

            for idx, g in enumerate(gates):
                # Drop identities immediately
                if isinstance(g, I):
                    to_delete.add(idx)
                    continue

                # Measurements are barriers; they just block
                if isinstance(g, M):
                    self._block_overlapping(stack, g.qubits)
                    continue

                # Compute keys
                qkey = self._qubits_key(g)
                fkey, invkey = self._forward_inverse_keys(g)

                if fkey is None:
                    # Unknown gate with no matrix; just block
                    self._block_overlapping(stack, g.qubits)
                    continue

                # If we previously saw an inverse on these qubits, cancel both
                inv_lookup = (invkey, qkey)
                if inv_lookup in stack:
                    prev_idx = stack.pop(inv_lookup)
                    to_delete.update((prev_idx, idx))
                    # Do not push current; pair is canceled
                    continue

                # Otherwise, this gate becomes the current candidate on these qubits
                self._block_overlapping(stack, g.qubits)
                stack[fkey, qkey] = idx

            if not to_delete:
                break

            gates = [gate for i, gate in enumerate(gates) if i not in to_delete]

        # Build new circuit (deepcopy to avoid Parameter sharing)
        out = Circuit(circuit.nqubits)
        for g in gates:
            out.add(deepcopy(g))

        self.append_circuit_to_context(out)
        return out

    # ----------------- key builders -----------------

    def _qubits_key(self, g: Gate) -> tuple[int, ...]:
        """Normalize qubit key for matching. CZ and SWAP are symmetric => unordered pair."""
        qs = g.qubits
        if isinstance(g, (CZ, SWAP)) and len(qs) == 2:
            a, b = qs
            return (a, b) if a < b else (b, a)
        # For Controlled (non-CZ), direction matters, so keep order (controls then targets)
        return qs

    def _forward_inverse_keys(self, g: Gate) -> tuple[Any | None, Any | None]:
        """
        Return (forward_key, inverse_key) for gate g.
        Keys are hashable and represent the unitary up to global phase.

        If we cannot build a key, return (None, None) so the caller treats g as a barrier.
        """
        # Self-inverse classes (no parameters)
        if isinstance(g, self._INVOLUTION_TYPES):
            # CZ/SWAP handled by unordered qubit key; CNOT is directional and self-inverse
            tag = type(g).__name__
            return (("INV", tag), ("INV", tag))

        # Parameterized rotations
        if isinstance(g, RX):
            a = _wrap_angle(g.theta)
            return (("RX", _round_f(a)), ("RX", _round_f(-a)))
        if isinstance(g, RY):
            a = _wrap_angle(g.theta)
            return (("RY", _round_f(a)), ("RY", _round_f(-a)))
        if isinstance(g, RZ):
            a = _wrap_angle(g.phi)
            return (("RZ", _round_f(a)), ("RZ", _round_f(-a)))
        if isinstance(g, U1):
            a = _wrap_angle(g.phi)
            return (("U1", _round_f(a)), ("U1", _round_f(-a)))
        if isinstance(g, U2):
            # Treat via U3 equivalence: U2(phi,gamma) == U3(pi/2, phi, gamma)
            theta, phi, gamma = (math.pi / 2.0, _wrap_angle(g.phi), _wrap_angle(g.gamma))
            return (
                ("U3", _round_f(theta), _round_f(phi), _round_f(gamma)),
                ("U3", _round_f(-theta), _round_f(-gamma), _round_f(-phi)),
            )
        if isinstance(g, U3):
            theta = _wrap_angle(g.theta)
            phi = _wrap_angle(g.phi)
            gamma = _wrap_angle(g.gamma)
            # U3(θ,φ,λ)† = U3(-θ, -λ, -φ)
            return (
                ("U3", _round_f(theta), _round_f(phi), _round_f(gamma)),
                ("U3", _round_f(-theta), _round_f(-gamma), _round_f(-phi)),
            )

        # Adjoint wrapper: swap forward/inverse of the base
        if isinstance(g, Adjoint):
            f, inv = self._forward_inverse_keys(g.basic_gate)
            return (inv, f)

        # Controlled: propagate keys with control count; direction matters
        if isinstance(g, Controlled):
            k = len(g.control_qubits)
            f_base, inv_base = self._forward_inverse_keys(g.basic_gate)
            if f_base is None:
                # Fallback to matrix signature
                return self._matrix_keys(g)
            return (("C", k, f_base), ("C", k, inv_base))

        # Generic w/ matrix fallback (includes Exponential, unknown 1Q BasicGate, etc.)
        f_inv = self._matrix_keys(g)
        return f_inv

    def _matrix_keys(self, g: Gate) -> tuple[Any | None, Any | None]:
        """Fallback: use unitary matrix signatures up to global phase."""
        U = _try_matrix(g)
        if U is None:
            return (None, None)
        sig = _dephased_signature(U)
        sig_inv = _dephased_signature(U.conj().T)
        return (("U", sig), ("U", sig_inv))

    # ----------------- blocking policy -----------------

    @staticmethod
    def _block_overlapping(
        stack: dict[tuple[Any, tuple[int, ...]], int],
        qubits: tuple[int, ...],
    ) -> None:
        """Drop any candidate whose qubits overlap with `qubits`."""
        if not qubits:
            stack.clear()
            return
        touched = set(qubits)
        for k in list(stack.keys()):
            _, k_qubits = k
            if touched.intersection(k_qubits):
                stack.pop(k, None)
