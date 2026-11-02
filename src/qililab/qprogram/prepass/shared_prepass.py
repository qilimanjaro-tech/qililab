# Copyright 2026 Qilimanjaro Quantum Tech
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

"""Pre-pass shared by every instrument compiler, run before the instrument pre-passes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.qprogram import QProgram


def prepare_shared(
    qprogram: QProgram, *, bus_mapping: dict[str, str] | None = None, calibration: Calibration | None = None
) -> QProgram:
    """Apply the bus mapping and the calibration, then check that every named operation is mapped.

    Args:
        qprogram (QProgram): The QProgram to prepare. It is not modified.
        bus_mapping (dict[str, str], optional): Mapping of the QProgram's bus names to the platform's. Defaults to None.
        calibration (Calibration, optional): Calibration resolving the named waveforms and weights. Defaults to None.

    Returns:
        QProgram: The prepared QProgram: a copy if a bus mapping or a calibration was applied, else ``qprogram`` itself.

    Raises:
        RuntimeError: If a named waveform or weight is still not mapped.
    """
    if bus_mapping is not None:
        qprogram = qprogram.with_bus_mapping(bus_mapping=bus_mapping)
    if calibration is not None:
        qprogram = qprogram.with_calibration(calibration=calibration)
    if qprogram.has_calibrated_waveforms_or_weights():
        raise RuntimeError(
            "Cannot compile to hardware-native instructions because QProgram contains named operations that are not mapped. Provide a calibration instance containing all necessary mappings."
        )
    return qprogram
