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
"""The operation ``qp.qblox.play()`` appends."""

from typing import ClassVar

from qprogram.operations import Operation
from qprogram.protocol import waveform_token
from qprogram.waveforms import IQWaveform, Waveform


class QbloxPlay(Operation):
    """A waveform played on a bus, where the Q1ASM ``play`` waits ``wait_time`` ns instead of the waveform's duration.

    qililab owns it: in a ``.qp`` file it reads ``qililab.qblox_play``.

    Args:
        bus (str): Identifier of the bus.
        waveform (Waveform | IQWaveform | str): The waveform, or the name of a calibrated one.
        wait_time (int): The ``wait_time`` of the Q1ASM ``play`` instruction, in ns.
    """

    WAVEFORM_ATTRS: ClassVar[tuple[str, ...]] = ("waveform",)

    def __init__(self, bus: str, waveform: Waveform | IQWaveform | str, wait_time: int) -> None:
        self.bus = bus
        self.waveform = waveform
        self.wait_time = wait_time

    def required_capabilities(self) -> set[str]:
        """Return ``vendor.qililab.qblox_play`` plus the tokens describing the waveform.

        Returns:
            set[str]: The capability tokens the operation needs.
        """
        caps = {"vendor.qililab.qblox_play"}
        if isinstance(self.waveform, str):
            caps.add("waveform.alias")
        else:
            caps.add("waveform.iq" if isinstance(self.waveform, IQWaveform) else "waveform.single")
            if (token := waveform_token(self.waveform)) is not None:
                caps.add(token)
        return caps
