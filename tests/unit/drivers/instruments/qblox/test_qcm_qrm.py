from unittest.mock import MagicMock

from qcodes.instrument import Instrument

from qililab.drivers.instruments.qblox.cluster import QcmQrm
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM

NUM_SUBMODULES = 6


def teardown_module():
    """Closes all instruments after tests terminate (either successfully or stop because of an error)."""
    Instrument.close_all()


class TestQcmQrm:
    """Unit tests checking the QililabQcmQrm attributes and methods"""

    def test_init(self):
        qcm_qrn_name = "qcm_qrm"
        sequencers_prefix = "sequencer"
        qcm_qrm = QcmQrm(parent=MagicMock(), name=qcm_qrn_name, slot_idx=0)
        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{qcm_qrn_name}_{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], SequencerQCM) for seq_idx in seq_idxs)
        assert expected_names == registered_names
