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

from copy import deepcopy
from typing import TYPE_CHECKING

from qililab.qprogram.blocks import Block
from qililab.waveforms import IQWaveform, Waveform

if TYPE_CHECKING:
    from qililab.qprogram.calibration import Calibration
    from qililab.qprogram.qprogram import QProgram


def prepare_qprogram(
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


def keep_instrument_operations(qprogram: QProgram, instrument_buses: set[str]) -> QProgram:
    """Return a copy of the QProgram with only the operations of one instrument: those on ``instrument_buses``.

    Every block is kept, even when it ends up empty, because the compilers rely on them as they relied on them when
    they walked the whole QProgram: the QDAC-II compiler multiplies the repetitions of a play by every loop it walks
    through, and the Qblox compiler emits a loop even with nothing inside. Operations without a bus (``qp.sync()``)
    are kept too: each compiler checks the buses they name.

    The compilers write into the operations they compile (e.g. the QDAC-II default dwell and repetitions, Qblox
    durations clamped to 4 ns): this copy is what keeps the caller's QProgram unchanged.

    Args:
        qprogram (QProgram): The QProgram to filter. It is not modified.
        instrument_buses (set[str]): All the buses of the instrument.

    Returns:
        QProgram: The filtered copy, whose ``buses`` are those of ``qprogram`` that are in ``instrument_buses``. It
        shares the waveforms of ``qprogram``: the compilers never modify a waveform (they copy one before splitting it),
        so its samples aren't duplicated.
    """

    def waveforms(block: Block):
        for element in block.elements:
            if isinstance(element, Block):
                yield from waveforms(element)
            else:
                yield from (value for value in vars(element).values() if isinstance(value, (Waveform, IQWaveform)))

    # deepcopy returns the objects already in its memo as they are
    copied_qprogram = deepcopy(qprogram, {id(waveform): waveform for waveform in waveforms(qprogram.body)})

    def traverse(block: Block) -> None:
        block.elements = [
            element
            for element in block.elements
            if isinstance(element, Block) or not hasattr(element, "bus") or element.bus in instrument_buses
        ]
        for element in block.elements:
            if isinstance(element, Block):
                traverse(element)

    traverse(copied_qprogram.body)
    copied_qprogram._buses = {bus for bus in copied_qprogram.buses if bus in instrument_buses}
    return copied_qprogram
