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

"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class DriveBus(BusDriver):
    """Qililab's driver for Drive Bus.

    Args:
        alias: Bus alias.
        port (int): Port to target.
        awg (AWG): Sequencer.
        local_oscillator (LocalOscillator | None): Local oscillator.
        attenuator (Attenuator | None): Attenuator.
        distortions (list): Distortions to apply in this Bus.

    Returns:
        BusDriver: BusDriver instance of type drive bus.
    """

    def __init__(
        self,
        alias: str,
        port: int,
        awg: AWG,
        local_oscillator: LocalOscillator | None,
        attenuator: Attenuator | None,
        distortions: list,
    ):
        super().__init__(alias=alias, port=port, awg=awg, distortions=distortions)
        if local_oscillator:
            self.instruments["local_oscillator"] = local_oscillator
        if attenuator:
            self.instruments["attenuator"] = attenuator
