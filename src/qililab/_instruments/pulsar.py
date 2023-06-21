from qblox_instruments.qcodes_drivers import Pulsar
from qililab._instruments import AWGSequencer

class QililabPulsar(Pulsar):
    def __init__(self, name: str, address: str | None = None, **kwargs):
        super().__init__(name, address, **kwargs)

        # Add sequencers
        sequencers = []
        for seq_idx in range(6):
            if self.is_qrm_type:
                sequencers.append(AWGDigitiserSequencer(self, f"sequencer{seq_idx}", seq_idx))
            else:
                sequencers.append(AWGSequencer(self, f"sequencer{seq_idx}", seq_idx))