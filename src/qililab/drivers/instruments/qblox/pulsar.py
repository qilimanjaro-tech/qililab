"""Driver for the Qblox Pulsar class."""
from qblox_instruments.qcodes_drivers import Pulsar as QcodesPulsar
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from qililab.instruments.utils import InstrumentFactory
from qililab.typings import InstrumentName

from .sequencer_qcm import SequencerQCM
from .sequencer_qrm import SequencerQRM


@InstrumentFactory.register
class Pulsar(QcodesPulsar):
    """Qililab's driver for QBlox-instruments Pulsar"""

    name = InstrumentName.PULSAR

    def __init__(self, name: str, address: str | None = None, **kwargs):
        """Initialise the instrument.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__(name, identifier=address, **kwargs)

        # Add sequencers
        self.submodules: dict[str, SequencerQCM | SequencerQRM] = {}  # resetting superclass submodules
        self.instrument_modules: dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: dict[str, ChannelTuple] = {}  # resetting superclass channel lists

        sequencer_class = SequencerQCM if self.is_qcm_type else SequencerQRM
        for seq_idx in range(6):
            seq = sequencer_class(parent=self, name=f"sequencer{seq_idx}", seq_idx=seq_idx)  # type: ignore
            self.add_submodule(f"sequencer{seq_idx}", seq)
