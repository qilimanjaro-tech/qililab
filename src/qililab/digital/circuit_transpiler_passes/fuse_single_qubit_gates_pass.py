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
from typing import TYPE_CHECKING, List, Tuple

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

from .circuit_transpiler_pass import CircuitTranspilerPass
from .numeric_helpers import (
    _is_close_mod_2pi,
    _mat_RX,
    _mat_RY,
    _mat_RZ,
    _mat_U3,
    _wrap_angle,
    _zyz_from_unitary,
)

if TYPE_CHECKING:
    import numpy as np


class FuseSingleQubitGatesPass(CircuitTranspilerPass):
    """
    Fuse maximal adjacent runs of 1-qubit gates per wire into a single gate:

      - If the fused unitary is a pure Z: emit RZ(phi).
      - Recognizable canonical forms: RY(theta) if (phi≈0, gamma≈0), RX(theta) if (phi≈-π/2, gamma≈π/2).
      - Otherwise emit a single U3(theta, phi, gamma).

    Boundaries that flush the pending 1-q block: CZ, SWAP, M (and any non-1q gate).
    Always returns a NEW circuit.
    """

    def run(self, circuit: Circuit) -> Circuit:
        seq_in = circuit.gates
        seq_out: List[Gate] = []
        pending: dict[int, np.ndarray] = {}

        def flush(q: int):
            if q not in pending:
                return
            U = pending.pop(q)
            theta, phi, gamma = _zyz_from_unitary(U)
            theta, phi, gamma = float(theta), float(phi), float(gamma)
            theta = _wrap_angle(theta)
            phi = _wrap_angle(phi)
            gamma = _wrap_angle(gamma)
            if _is_close_mod_2pi(theta, 0.0):
                # pure Z: RZ(ph + lam)
                seq_out.append(RZ(q, phi=_wrap_angle(phi + gamma)))
                return
            if _is_close_mod_2pi(phi, 0.0) and _is_close_mod_2pi(gamma, 0.0):
                seq_out.append(RY(q, theta=theta))
                return
            if _is_close_mod_2pi(phi, math.pi) and _is_close_mod_2pi(gamma, math.pi):
                seq_out.append(RY(q, theta=-theta))
                return
            if _is_close_mod_2pi(phi, -math.pi / 2.0) and _is_close_mod_2pi(gamma, math.pi / 2.0):
                seq_out.append(RX(q, theta=theta))
                return
            if _is_close_mod_2pi(phi, math.pi / 2.0) and _is_close_mod_2pi(gamma, -math.pi / 2.0):
                seq_out.append(RX(q, theta=-theta))
                return
            seq_out.append(U3(q, theta=theta, phi=phi, gamma=gamma))

        def apply(q: int, U: np.ndarray):
            pending[q] = U @ pending[q] if q in pending else U

        def flush_touches(qubits: Tuple[int, ...]):
            for q in qubits:
                flush(q)

        for g in seq_in:
            if isinstance(g, (U3, RX, RY, RZ)):
                q = g.qubits[0]
                if isinstance(g, U3):
                    U = _mat_U3(g.theta, g.phi, g.gamma)
                elif isinstance(g, RX):
                    U = _mat_RX(g.theta)
                elif isinstance(g, RY):
                    U = _mat_RY(g.theta)
                else:  # RZ
                    U = _mat_RZ(g.phi)
                apply(q, U)

            elif isinstance(g, CZ):
                flush_touches((*g.control_qubits, *g.target_qubits))
                seq_out.append(g)

            elif isinstance(g, SWAP):
                flush_touches(g.target_qubits)
                seq_out.append(g)

            elif isinstance(g, M):
                flush_touches(g.qubits)
                seq_out.append(g)

            else:
                # Unknown/non-1q: be conservative and flush any involved qubits
                flush_touches(g.qubits)
                seq_out.append(g)

        # flush any remaining
        for q in list(pending.keys()):
            flush(q)

        out = Circuit(circuit.nqubits)
        for g in seq_out:
            out.add(g)

        self.append_circuit_to_context(out)
        return out
