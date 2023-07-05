from typing import Dict, Union

from qblox_instruments.qcodes_drivers import Pulsar as QcodesPulsar
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from .sequencer import AWGSequencer


class Pulsar(QcodesPulsar):
    """Qililab's driver for QBlox-instruments Pulsar"""

    def __init__(self, name: str, address: str | None = None, **kwargs):
        """Initialise the instrument.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__(name, identifier=address, **kwargs)

        # Add sequencers
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: Dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: Dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)
