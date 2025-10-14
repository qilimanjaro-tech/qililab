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

from typing import TYPE_CHECKING, Optional, Union

from qilisdk.digital import Circuit
from qilisdk.digital.gates import CZ, RZ, M

from qililab.digital.native_gates import Rmw

from .circuit_transpiler_pass import CircuitTranspilerPass
from .numeric_helpers import _wrap_angle

if TYPE_CHECKING:
    from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings
    from qililab.settings.digital.gate_event import GateEvent


class AddPhasesToRmwFromRZAndCZPass(CircuitTranspilerPass):
    """Fold all Z-axis phases from RZs and CZ phase-corrections into subsequent resonant
    microwave rotations (Rmw) as *virtual-Z* updates applied directly to the pulse phase.

    Key points:
      - RZ(φ) commuting forward adds +φ to the axis of every later XY pulse on that qubit.
      - CZ calibration may specify per-qubit phase corrections; we accumulate both.
      - The per-qubit Z-frame persists; do NOT reset it after an Rmw.
      - Any residual Z-frame at the end is irrelevant to Z-basis measurement, so RZs can be deleted.

    Sign convention:
      Because the VZ is realized by rotating the *pulse* (logical axis) rather than an NCO frame,
      the phase we emit for an Rmw becomes: phase_out = wrap(gate.phase + shift[q]).

    Phases are wrapped to [-π, π) for numerical hygiene.
    For background on persistent virtual-Z / frame updates, see https://arxiv.org/abs/1612.00858
    """

    def __init__(self, settings: DigitalCompilationSettings) -> None:
        self._settings = settings

    def run(self, circuit: Circuit) -> Circuit:
        nqubits = circuit.nqubits
        circuit_gates = circuit.gates

        out_circuit = Circuit(nqubits)
        shift: dict[int, float] = dict.fromkeys(range(nqubits), 0.0)

        for gate in circuit_gates:
            out_gate: Optional[Union[M, Rmw, CZ]] = None

            # Accumulate phase shifts from commutating RZ to the end, to discard them as VirtualZ.
            if isinstance(gate, RZ):
                qubit = gate.target_qubits[0]
                shift[qubit] = _wrap_angle(shift[qubit] + gate.phi)

            # Pass through CZ, while accumulating its per-qubit phase corrections
            elif isinstance(gate, CZ):
                control_qubit, target_qubit = gate.control_qubits[0], gate.target_qubits[0]
                gate_settings = self._settings.get_gate(name="CZ", qubits=(control_qubit, target_qubit))
                gate_corrections = self._extract_gate_corrections(gate_settings, control_qubit, target_qubit)
                shift[control_qubit] = _wrap_angle(shift[control_qubit] + gate_corrections[f"q{control_qubit}_phase_correction"])
                shift[target_qubit] = _wrap_angle(shift[target_qubit] + gate_corrections[f"q{target_qubit}_phase_correction"])
                out_gate = CZ(control_qubit, target_qubit)

             # Apply VZ by rotating the *pulse* axis: phase_out = phase_in + shift[q]
            elif isinstance(gate, Rmw):
                qubit = gate.qubits[0]
                out_gate = Rmw(qubit, theta=gate.theta, phase=_wrap_angle(gate.phase + shift[qubit]))

            # Measurement gates, do not change
            elif isinstance(gate, M):
                out_gate = M(*gate.qubits)

            # If gate is not supported, raise an error
            else:
                raise ValueError(
                    f"Unsupported gate {gate!r} (name={getattr(gate, 'name', type(gate).__name__)}) "
                    f"— supported: {RZ.__name__}, {Rmw.__name__}, {CZ.__name__}, {M.__name__}"
                )

            # Add the processed gate to the output circuit
            if out_gate is not None:
                out_circuit.add(out_gate)

        # (Residual Z-frames are harmless; measurement in Z basis is invariant.)
        self.append_circuit_to_context(out_circuit)
        return out_circuit

    @staticmethod
    def _extract_gate_corrections(
        gate_settings: list[GateEvent], c: int, t: int
    ) -> dict[str, float]:
        """
        Given a CZ gate's settings, extract any present per-qubit phase corrections.
        Returns a dict with zero defaults if not present.
        Expected keys: f"q{c}_phase_correction", f"q{t}_phase_correction" (radians).
        """
        corr = {
            f"q{c}_phase_correction": 0.0,
            f"q{t}_phase_correction": 0.0,
        }
        # Find the first event containing at least one relevant key
        for event in gate_settings or []:
            opts = getattr(event, "options", None)
            if not isinstance(opts, dict):
                continue
            updated = False
            key_c = f"q{c}_phase_correction"
            key_t = f"q{t}_phase_correction"
            if key_c in opts and isinstance(opts[key_c], (int, float)):
                corr[key_c] = float(opts[key_c])
                updated = True
            if key_t in opts and isinstance(opts[key_t], (int, float)):
                corr[key_t] = float(opts[key_t])
                updated = True
            if updated:
                break
        return corr
