from qblox_instruments.qcodes_drivers import Cluster
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qililab.drivers import QililabQcmQrm
from typing import Dict, Union


class QililabCluster(Cluster):
    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, **kwargs)

        # Add qcm-qrm's to the cluster
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {} # resetting superclass submodules
        for slot_idx in range(1, self._num_slots + 1):
            module = QililabQcmQrm(self, "module{}".format(slot_idx), slot_idx)
            self.add_submodule("module{}".format(slot_idx), module)
