from typing import Dict, Union

from qblox_instruments.qcodes_drivers import Cluster as QcodesCluster
from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm as QcodesQcmQrm
from qcodes import Instrument
from qcodes.instrument.channel import ChannelTuple, InstrumentModule

from .sequencer_qcm import SequencerQCM
from .sequencer_qrm import SequencerQRM


class Cluster(QcodesCluster):
    """Qililab's driver for QBlox-instruments Cluster"""

    def __init__(self, name: str, address: str | None = None, **kwargs):
        """Initialise the instrument.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__(name, identifier=address, **kwargs)

        # Add qcm-qrm's to the cluster
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: Dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: Dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        # registering only the slots specified in the dummy config if that is the case
        if "dummy_cfg" in kwargs:
            slot_ids = list(kwargs["dummy_cfg"].keys())
        else:
            slot_ids = list(range(1, self._num_slots + 1))

        for slot_idx in slot_ids:
            module = QcmQrm(self, f"module{slot_idx}", slot_idx)
            self.add_submodule(f"module{slot_idx}", module)


class QcmQrm(QcodesQcmQrm):
    """Qililab's driver for QBlox-instruments QcmQrm"""

    def __init__(self, parent: Instrument, name: str, slot_idx: int):
        """Initialise the instrument.

        Args:
            parent (Instrument): Instrument´s parent
            name (str): Name of the instrument
            slot_idx (int): Index of the slot
        """
        super().__init__(parent, name, slot_idx)

        # Add sequencers
        self.submodules: dict[str, Union[InstrumentModule, ChannelTuple]] = {}  # resetting superclass submodules
        self.instrument_modules: Dict[str, InstrumentModule] = {}  # resetting superclass instrument modules
        self._channel_lists: Dict[str, ChannelTuple] = {}  # resetting superclass channel lists
        sequencer_class = SequencerQCM if self.is_qcm_type else SequencerQRM
        for seq_idx in range(6):
            seq = sequencer_class(parent=self, name=f"sequencer{seq_idx}", seq_idx=seq_idx)  # type: ignore
            self.add_submodule(f"sequencer{seq_idx}", seq)
