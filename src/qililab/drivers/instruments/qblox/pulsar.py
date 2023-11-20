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

"""Driver for the Qblox Pulsar class."""
from qblox_instruments.qcodes_drivers import Pulsar as QcodesPulsar
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces.base_instrument import BaseInstrument

from .sequencer_qcm import SequencerQCM
from .sequencer_qrm import SequencerQRM


@InstrumentDriverFactory.register
class Pulsar(QcodesPulsar, BaseInstrument):  # pylint: disable=abstract-method
    """Qililab's driver for QBlox-instruments Pulsar

    Args:
        name (str): Sequencer name
        address (str): Instrument address
    """

    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, identifier=address, **kwargs)

        # Add sequencers
        self.submodules: dict[str, SequencerQCM | SequencerQRM] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists

        sequencer_class = SequencerQCM if self.is_qcm_type else SequencerQRM
        for seq_idx in range(6):
            seq = sequencer_class(parent=self, name=f"sequencer{seq_idx}", seq_idx=seq_idx)  # type: ignore
            self.add_submodule(f"sequencer{seq_idx}", seq)

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name
