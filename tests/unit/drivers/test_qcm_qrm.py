from qcodes.tests.instrument_mocks import DummyInstrument
from qililab.drivers.instruments.qblox.cluster import QcmQrm
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer
from unittest.mock import MagicMock

NUM_SUBMODULES = 6

class MockQcmQrm(DummyInstrument):

    def __init__(self, parent, name, slot_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {'test_submodule':MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False
        
class MockCluster(DummyInstrument):

    def __init__(self, name, address=None, **kwargs):
        super().__init__(name, **kwargs)

        self.address = address
        self.submodules = {'test_submodule':MagicMock()}


class TestQcmQrm:
    """Unit tests checking the QililabQcmQrm attributes and methods"""

    def test_init(self):
        QcmQrm.__bases__ = (MockQcmQrm,)
        qcm_qrn_name = "test_qcm_qrm"
        sequencers_prefix = "sequencer"
        cluster = MockCluster(name="test_cluster")
        qcm_qrm = QcmQrm(parent=cluster, name=qcm_qrn_name, slot_idx=0)
        submodules = qcm_qrm.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f'{qcm_qrn_name}_{sequencers_prefix}{idx}' for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]
        
        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], AWGSequencer) for seq_idx in seq_idxs)
        assert (expected_names == registered_names)
