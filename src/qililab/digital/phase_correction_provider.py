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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qilisdk.digital.circuit_transpiler_passes import PhaseCorrectionProvider

    from qililab.settings.digital.digital_compilation_settings import DigitalCompilationSettings
    from qililab.settings.digital.gate_event import GateEvent


def extract_cz_phase_corrections(gate_settings: list[GateEvent], control: int, target: int) -> tuple[float, float]:
    """Extract per-qubit CZ phase corrections from a gate's settings events.

    Returns ``(control_correction, target_correction)`` in radians, with zero defaults
    when no event in ``gate_settings`` provides the relevant ``q{c}_phase_correction``
    or ``q{t}_phase_correction`` option.
    """
    key_c = f"q{control}_phase_correction"
    key_t = f"q{target}_phase_correction"
    correction_c = 0.0
    correction_t = 0.0

    for event in gate_settings or []:
        opts = getattr(event, "options", None)
        if not isinstance(opts, dict):
            continue
        updated = False
        if key_c in opts and isinstance(opts[key_c], (int, float)):
            correction_c = float(opts[key_c])
            updated = True
        if key_t in opts and isinstance(opts[key_t], (int, float)):
            correction_t = float(opts[key_t])
            updated = True
        if updated:
            break

    return correction_c, correction_t


def build_phase_correction_provider(settings: DigitalCompilationSettings) -> PhaseCorrectionProvider:
    """Build a ``PhaseCorrectionProvider`` callable from a ``DigitalCompilationSettings``.

    The returned callable looks up the CZ gate settings for ``(control, target)`` and
    returns the per-qubit phase corrections recorded in its options.
    """

    def provider(control: int, target: int) -> tuple[float, float]:
        gate_settings = settings.get_gate(name="CZ", qubits=(control, target))
        return extract_cz_phase_corrections(gate_settings, control, target)

    return provider
