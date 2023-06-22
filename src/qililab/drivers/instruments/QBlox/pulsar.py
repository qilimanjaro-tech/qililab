from qblox_instruments.qcodes_drivers import Pulsar
from qililab.drivers import AWGSequencer

class QililabPulsar(Pulsar):
    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, **kwargs)

        # Add sequencers
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)