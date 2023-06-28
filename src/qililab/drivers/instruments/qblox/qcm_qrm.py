from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm as QcodesQcmQrm
from qcodes import Instrument
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer
from typing import Dict, Union


class QcmQrm(QcodesQcmQrm):
    """Qililab's driver for QBlox-instruments QcmQrm"""
    
    def __init__(self, parent: Instrument, name: str, slot_idx: int, **kwargs):
        """Initialise the instrument.

        Args:
            parent (Instrument): Instrument´s parent
            name (str): Name of the instrument
            slot_idx (int): Index of the slot
        """
        super().__init__(parent, name, slot_idx)

        # Add sequencers
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {}
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)
