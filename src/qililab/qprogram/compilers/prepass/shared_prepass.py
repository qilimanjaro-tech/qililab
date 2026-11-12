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
"""Pre-pass shared by every instrument compiler, run before the instrument pre-passes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import qprogram as qp
from qprogram.blocks import Block
from qprogram_qblox import WaitTrigger as QbloxWaitTrigger
from qprogram_qdac import WaitTrigger as QdacWaitTrigger

from qililab.qprogram.blocks import IfTrigger, reject_variables_swept_by_enclosing_loops
from qililab.qprogram.operations.disable_autosync import DisableAutosync
from qililab.qprogram.operations.measure_reset import MeasureReset
from qililab.qprogram.profiles import QILILAB_QBLOX_PARITY_V1

if TYPE_CHECKING:
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
        VariableAllocated: If a loop sweeps a variable an enclosing loop already sweeps.
        ValueError: If a ``qililab.disable_autosync`` is inside a block instead of at the top of the body.
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
    _reject_nested_loops_on_one_variable(qprogram.body, [])
    _reject_nested_disable_autosync(qprogram)
    validate(qprogram)
    return qprogram


def _reject_nested_disable_autosync(qprogram: QProgram) -> None:
    """Raise if a ``qililab.disable_autosync`` is inside a block: it is a setting of the whole program.

    ``qp.qblox.disable_autosync`` only ever puts it at the top of the body; this covers programs read from ``.qp``.

    Args:
        qprogram (QProgram): The QProgram to check.

    Raises:
        ValueError: If a ``qililab.disable_autosync`` is inside a block.
    """
    for element in qprogram.body.elements:
        if isinstance(element, Block) and any(isinstance(node, DisableAutosync) for node in element.walk()):
            raise ValueError(
                "qililab.disable_autosync applies to the whole program: it can only be at the top of the body, not "
                "inside a block. Set it with qp.qblox.disable_autosync = True."
            )


def _reject_nested_loops_on_one_variable(block: Block, enclosing: list[Block]) -> None:
    """Raise if a loop sweeps a variable that an enclosing loop already sweeps.

    The builder checks it as the loops open; this covers programs it did not build, such as ones read from ``.qp``.

    Args:
        block (Block): The block to check.
        enclosing (list[Block]): The blocks around ``block``.

    Raises:
        VariableAllocated: If a loop in ``block`` sweeps a variable an enclosing loop already sweeps.
    """
    for element in block.elements:
        if isinstance(element, Block):
            reject_variables_swept_by_enclosing_loops(element, [*enclosing, block])
            _reject_nested_loops_on_one_variable(element, [*enclosing, block])


def validate(qprogram: QProgram) -> None:
    """Validate ``qprogram`` against qililab's capability profile, ``qililab-qblox-parity-v1``.

    Args:
        qprogram (QProgram): The QProgram to validate.

    Raises:
        ValidationError: If the program uses something qililab does not support, listing every error found.
    """
    diagnostics, _ = qp.validate(qprogram, QILILAB_QBLOX_PARITY_V1)
    errors = [diagnostic for diagnostic in diagnostics if diagnostic.severity == "error"]
    # A Qblox operation another check rejects also gets a "missing-capability" for the QDAC half of its bus, which
    # only says the QDAC can't run it either: keep the error that says why.
    explained = {id(error.node) for error in errors if error.code != "missing-capability" and error.node is not None}
    errors = [
        error
        for error in errors
        if not (error.code == "missing-capability" and id(error.node) in explained and "(rt)" not in error.message)
    ]
    if errors:
        raise qp.ValidationError(
            "The QProgram uses features qililab does not support:\n" + "\n".join(str(error) for error in errors)
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
