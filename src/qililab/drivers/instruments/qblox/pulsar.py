from qblox_instruments.qcodes_drivers import Pulsar as QcodesPulsar
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qililab.drivers import AWGSequencer
from typing import Dict, Union


class QililabPulsar(QcodesPulsar):
    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, **kwargs)

        # Add sequencers
        self.submodules: Dict[str, Union[InstrumentModule, ChannelTuple]] = {} # resetting superclass submodules
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)
