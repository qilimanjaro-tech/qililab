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
"""The operation ``qp.qblox.measure_reset()`` appends."""

from collections.abc import Iterable
from typing import ClassVar

from qprogram import MeasurementHandle
from qprogram.operations.operation import MeasurementField, MeasurementOperation, normalize_fields
from qprogram.protocol import waveform_token
from qprogram.waveforms import IQWaveform


class MeasureReset(MeasurementOperation):
    """A measurement followed by a reset pulse on ``control_bus`` when the thresholded result is 1 (active reset).

    A measurement like ``acquire``, so it takes a name from the program's measurement counter and its results come
    back under its handle. qililab owns it: in a ``.qp`` file it reads ``qililab.measure_reset``.

    Args:
        bus (str): Identifier of the measurement bus.
        waveform (IQWaveform | str): Waveform played during measurement, or the name of a calibrated one.
        weights (IQWaveform | str): Weights used for integration, or the name of calibrated ones.
        control_bus (str): Identifier of the control bus the reset pulse is played on.
        reset_pulse (IQWaveform | str): Pulse used for active reset, or the name of a calibrated one.
        handle (MeasurementHandle): The handle the results are stored under.
        trigger_address (int, optional): Trigger network address the result is sent on. Defaults to 1.
        fields (Iterable[MeasurementField], optional): The measurement fields to return. Defaults to ``(IQ,)``.
    """

    BUS_ATTRS: ClassVar[tuple[str, ...]] = ("bus", "control_bus")
    WAVEFORM_ATTRS: ClassVar[tuple[str, ...]] = ("waveform", "weights", "reset_pulse")

    def __init__(
        self,
        bus: str,
        waveform: IQWaveform | str,
        weights: IQWaveform | str,
        control_bus: str,
        reset_pulse: IQWaveform | str,
        handle: MeasurementHandle,
        trigger_address: int = 1,
        fields: Iterable[MeasurementField] = (MeasurementField.IQ,),
    ) -> None:
        self.bus = bus
        self.waveform = waveform
        self.weights = weights
        self.control_bus = control_bus
        self.reset_pulse = reset_pulse
        self.handle = handle
        self.trigger_address = trigger_address
        self.fields: tuple[str, ...] = normalize_fields(fields)

    def required_capabilities(self) -> set[str]:
        """Return ``vendor.qililab.measure_reset`` plus the waveform and requested-field tokens.

        Returns:
            set[str]: The capability tokens the operation needs.
        """
        caps = super().required_capabilities() | {"vendor.qililab.measure_reset", "waveform.iq"}
        for waveform in (self.waveform, self.weights, self.reset_pulse):
            if isinstance(waveform, str):
                caps.add("waveform.alias")
            elif (token := waveform_token(waveform)) is not None:
                caps.add(token)
        return caps
