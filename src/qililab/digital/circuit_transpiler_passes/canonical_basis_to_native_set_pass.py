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

from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CZ,
    RX,
    RY,
    RZ,
    U3,
    Gate,
    M,
)

from qililab.digital.native_gates import Drag

from .circuit_transpiler_pass import CircuitTranspilerPass
from .numeric_helpers import _wrap_angle


class CanonicalBasisToNativeSetPass(CircuitTranspilerPass):
    """
    Lower from the canonical basis {CZ, U3, RX, RY, RZ, M, SWAP}
    to the native set {Drag, CZ, M} (+ optional virtual RZ).

    Mapping:
      - U3(theta, phi, gamma)   → Drag(theta, phase=-gamma+pi/2) ; RZ(phi+gamma)
      - RX(theta)               → Drag(theta, phase=0)
      - RY(theta)               → Drag(theta, phase=pi/2)
      - CZ                      → CZ
      - M                       → M

    Options:
      - keep_virtual_rz: keep RZ as a virtual Z (default True).
      - merge_consecutive_rz: sum consecutive RZ on each wire (default True).
      - drop_rz_before_measure: drop any pending RZ on measured qubits (default True).
      - angle_tol: numerical tolerance for dropping near-zero angles.
    """

    def __init__(
        self,
        *,
        keep_virtual_rz: bool = True,
        merge_consecutive_rz: bool = True,
        drop_rz_before_measure: bool = True,
        angle_tol: float = 1e-12,
    ) -> None:
        self.keep_virtual_rz = keep_virtual_rz
        self.merge_consecutive_rz = merge_consecutive_rz
        self.drop_rz_before_measure = drop_rz_before_measure
        self.angle_tol = float(angle_tol)

    # ---------------- public API ----------------

    def run(self, circuit: Circuit) -> Circuit:
        out = Circuit(circuit.nqubits)

        # Pending virtual Z rotation per qubit (for simple RZ merging / scheduling)
        pending_rz: dict[int, float] = {}

        def emit_rz(q: int) -> None:
            """Flush a pending RZ on q, if any (and if we keep RZ at all)."""
            if not self.keep_virtual_rz:
                pending_rz.pop(q, None)
                return
            if q in pending_rz:
                phi = _wrap_angle(pending_rz[q])
                pending_rz.pop(q, None)
                if abs(phi) > self.angle_tol:
                    out.add(RZ(q, phi=phi))

        def touch(*qubits: int) -> None:
            """Before emitting any non-commuting gate on given qubits, flush their pending RZ."""
            for q in qubits:
                emit_rz(q)

        def add_rz(q: int, phi: float) -> None:
            """Accumulate a virtual Z on q (merged later)."""
            if not self.keep_virtual_rz:
                return
            if self.merge_consecutive_rz:
                pending_rz[q] = _wrap_angle(pending_rz.get(q, 0.0) + phi)
            else:
                emit_rz(q)
                if abs(phi) > self.angle_tol:
                    out.add(RZ(q, phi=_wrap_angle(phi)))

        def lower_1q_as_Drag_RZ(g: Gate) -> None:
            q = g.qubits[0]
            if isinstance(g, RX):
                touch(q)
                out.add(Drag(q, theta=g.theta, phase=0.0))
            elif isinstance(g, RY):
                touch(q)
                out.add(Drag(q, theta=g.theta, phase=math.pi / 2.0))
            elif isinstance(g, RZ):
                add_rz(q, g.phi)
            elif isinstance(g, U3):
                # U3(theta, phi, gamma) with U3 = RZ(phi) RY(theta) RZ(gamma)
                touch(q)
                out.add(Drag(q, theta=g.theta, phase=_wrap_angle(g.phi + math.pi / 2)))
                add_rz(q, _wrap_angle(g.phi + g.gamma))

            else:
                raise NotImplementedError(f"Unexpected 1-qubit gate in native lowering: {type(g).__name__}")

        for g in circuit.gates:
            # 1-qubit gates
            if isinstance(g, (U3, RX, RY, RZ)):
                lower_1q_as_Drag_RZ(g)
                continue

            # 2-qubit entangler
            if isinstance(g, CZ):
                # Z-rotations commute with CZ; we *could* leave them pending.
                # For determinism, we simply emit CZ now without flushing.
                out.add(CZ(g.control_qubits[0], g.target_qubits[0]))
                continue

            # Measurement
            if isinstance(g, M):
                if self.drop_rz_before_measure:
                    # Drop any pending Z on measured qubits (no effect on Z-basis measurement)
                    for q in g.qubits:
                        pending_rz.pop(q, None)
                else:
                    # Ensure phase is applied before M
                    for q in g.qubits:
                        emit_rz(q)
                out.add(M(*g.qubits))
                continue

            raise NotImplementedError(f"Gate {type(g).__name__} is not supported at this lowering stage.")

        # Flush any remaining pending Z
        for q in pending_rz:
            emit_rz(q)

        self.append_circuit_to_context(out)

        return out
