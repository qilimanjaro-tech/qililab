from qblox_instruments.qcodes_drivers.qcm_qrm import QcmQrm
from qcodes import Instrument
from qililab.drivers import AWGSequencer


class QililabQcmQrm(QcmQrm):
    def __init__(self, parent: Instrument, name: str, slot_idx: int, address: str | None = None, **kwargs):
        super().__init__(parent, name, slot_idx)

        # Add sequencers
        for seq_idx in range(6):
            seq = AWGSequencer(self, f"sequencer{seq_idx}", seq_idx)
            self.add_submodule(f"sequencer{seq_idx}", seq)