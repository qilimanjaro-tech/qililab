"""Driver for the Drive Bus class."""
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qcodes.metadatable import Metadatable
from qililab.buses.instruments.bus import GenericBus
from qililab.buses.interfaces import BusInterface
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM

class DriveBus(GenericBus, BusInterface):
    """Qililab's driver for Drive Bus"""

    def __init__(self, qubit:int, sequencer_class: str, has_lo: bool=False, has_attenuator: bool=False, **kwargs):
        """Initialise the bus.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__(**kwargs)
        # Add instruments to bus
        seq_idx = 0
        sequencer = SequencerQCM(parent=self, name=f"sequencer{seq_idx}", seq_idx=seq_idx)  # type: ignore
        self.add_submodule(f"sequencer{seq_idx}", sequencer) 
