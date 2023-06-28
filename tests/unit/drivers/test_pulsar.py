from qblox_instruments.types import PulsarType
from qililab.drivers.instruments.qblox.pulsar import Pulsar
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer

NUM_SUBMODULES = 6

class TestPulsar:
    """Unit tests checking the QililabPulsar attributes and methods"""
    
    def test_init(self):
        pulsar = Pulsar(name="test", dummy_type=PulsarType.PULSAR_QCM)
        submodules = pulsar.submodules
        seq_idxs = list(submodules.keys())
        
        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], AWGSequencer) for seq_idx in seq_idxs)
