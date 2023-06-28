from qblox_instruments.qcodes_drivers import Cluster as QcodesCluster
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from .qcm_qrm import QcmQrm
from typing import Dict, Union


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
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {} # resetting superclass submodules
        self.instrument_modules: Dict[str, InstrumentModule] = {} # resetting superclass instrument modules
        self._channel_lists: Dict[str, ChannelTuple] = {} # resetting superclass channel lists
        # registering only the slots specified in the dummy config if that is the case
        if 'dummy_cfg' in kwargs:
            slot_ids = list(kwargs['dummy_cfg'].keys())
        else:
            slot_ids = [i for i in range(1, self._num_slots+1)]
            
        for slot_idx in slot_ids:
            module = QcmQrm(self, "module{}".format(slot_idx), slot_idx)
            self.add_submodule("module{}".format(slot_idx), module)
