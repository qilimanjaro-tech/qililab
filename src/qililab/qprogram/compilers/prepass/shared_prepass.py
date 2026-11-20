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

import qprogram as qp
from qprogram_qblox import WaitTrigger as QbloxWaitTrigger
from qprogram_qdac import WaitTrigger as QdacWaitTrigger

from qililab.qprogram.blocks import IfTrigger
from qililab.qprogram.operations.measure_reset import MeasureReset
from qililab.qprogram.profiles import QILILAB_QBLOX_PARITY_V1

if TYPE_CHECKING:
    from qprogram.protocol import PlatformCapabilities

    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.qprogram import QProgram


def prepare_shared(
    qprogram: QProgram, *, bus_mapping: dict[str, str] | None = None, calibration: Calibration | None = None
) -> QProgram:
    """Apply the bus mapping and the calibration, check every named operation is mapped, and validate the program.

    The program is validated against qililab's capability profile, ``qililab-qblox-parity-v1``: anything qililab
    cannot run fails here.

    Args:
        qprogram (QProgram): The QProgram to prepare. It is not modified.
        bus_mapping (dict[str, str], optional): Mapping of the QProgram's bus names to the platform's. Defaults to None.
        calibration (Calibration, optional): Calibration resolving the named waveforms and weights. Defaults to None.

    Returns:
        QProgram: The prepared QProgram: a copy if a bus mapping or a calibration was applied, else ``qprogram`` itself.

    Raises:
        RuntimeError: If a named waveform or weight is still not mapped.
        NotImplementedError: If ``qp.if_trigger()`` is used together with a wait for a trigger or a
            ``qp.qblox.measure_reset()``.
        ValidationError: If the program uses something qililab does not support.
    """
    if bus_mapping is not None:
        qprogram = qprogram.with_bus_mapping(bus_mapping=bus_mapping)
    if calibration is not None:
        qprogram = qprogram.with_calibration(calibration=calibration)
    if qprogram.has_calibrated_waveforms_or_weights():
        raise RuntimeError(
            "Cannot compile to hardware-native instructions because QProgram contains named operations that are not mapped. Provide a calibration instance containing all necessary mappings."
        )
    _reject_if_trigger_with_other_trigger_modes(qprogram)
    validate(qprogram)
    return qprogram


def validate(program: qp.QProgram, capabilities: PlatformCapabilities = QILILAB_QBLOX_PARITY_V1) -> None:
    """Validate ``program`` against one of qililab's capability profiles.

    Args:
        program (qp.QProgram): The QProgram, or the Experiment, to validate.
        capabilities (PlatformCapabilities, optional): What qililab runs. Defaults to ``qililab-qblox-parity-v1``, the
            QPrograms' profile.

    Raises:
        ValidationError: If the program uses something qililab does not support, listing every error found.
    """
    diagnostics, _ = qp.validate(program, capabilities)
    errors = [diagnostic for diagnostic in diagnostics if diagnostic.severity == "error"]
    if errors:
        raise qp.ValidationError(
            f"The {type(program).__name__} uses features qililab does not support:\n"
            + "\n".join(str(error) for error in errors)
        )


def _reject_if_trigger_with_other_trigger_modes(qprogram: QProgram) -> None:
    """Raise if ``qp.if_trigger()`` is used together with a wait for a trigger or a ``qp.qblox.measure_reset()``.

    Only one hardware-trigger mechanism can gate real-time execution per QProgram: ``if_trigger()`` is mutually
    exclusive with the other two, which are not mutually exclusive with each other.

    Args:
        qprogram (QProgram): The QProgram to check.

    Raises:
        NotImplementedError: If ``if_trigger()`` is used with ``wait_trigger`` or ``qp.qblox.measure_reset()``.
    """
    nodes = list(qprogram.body.walk())
    if not any(isinstance(node, IfTrigger) for node in nodes):
        return
    for node in nodes:
        if isinstance(node, (QbloxWaitTrigger, QdacWaitTrigger)):
            raise NotImplementedError("if_trigger() cannot be used together with wait_trigger in the same QProgram.")
        if isinstance(node, MeasureReset):
            raise NotImplementedError(
                "if_trigger() cannot be used together with qp.qblox.measure_reset() in the same QProgram."
            )
