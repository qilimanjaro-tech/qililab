# Copyright 2025 Qilimanjaro Quantum Tech
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

from typing import TYPE_CHECKING, Any, Tuple

from qcodes import VisaInstrument
from qcodes.validators import Enum

if TYPE_CHECKING:
    from qcodes.parameters import Parameter

_CHANNELS: Tuple[str, ...] = tuple(f"{r}{i}" for i in range(1, 17) for r in ["RF", "rf"])


class DriverRSWUSP16TR(VisaInstrument):
    """
    QCoDeS driver for the Becker Nachrichtentechnik RSWU-SP16TR RF switch.

    Notes
    -----
    * Use raw socket VISA address: 'TCPIP::<IP>::5025::SOCKET'
    * Device uses LF ('\\n') as line termination.
    * Only one output channel can be active at a time.
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name, address, terminator="\n", **kwargs)

        self.idn: Parameter = self.add_parameter(
            "idn",
            label="Identification",
            get_cmd="*IDN?",
            get_parser=str,
        )
        """Parameter idn"""

        self.active_channel: Parameter = self.add_parameter(
            "active_channel",
            label="Active RF output",
            vals=Enum(*_CHANNELS),
            get_cmd="ROUT:CHAN?",
            set_cmd="ROUT:CHAN {}",
            get_parser=self._parse_active_channel,
            docstring="Currently routed output port (RF1..RF16).",
        )
        """Parameter active_channel"""

        self.connect_message()

    @staticmethod
    def _parse_active_channel(reply: str) -> str:
        rep = reply.strip().upper()
        if rep in _CHANNELS:
            return rep
        if rep.isdigit():
            idx = int(rep)
            if 1 <= idx <= 16:
                return f"RF{idx}"
        return rep  # fallback

    def route(self, channel: str) -> None:
        """Route to a specific RF output (RF1..RF16)."""
        self.active_channel(channel)

    def close(self) -> None:
        super().close()
