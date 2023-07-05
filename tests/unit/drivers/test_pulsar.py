from qblox_instruments.types import PulsarType
from qcodes import Instrument
from qililab.drivers.instruments.qblox.pulsar import Pulsar
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer

NUM_SUBMODULES = 6


class TestPulsar:
    """Unit tests checking the QililabPulsar attributes and methods"""

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()

    def test_init(self):
        pulsar_name = "test"
        sequencers_prefix = "sequencer"
        pulsar = Pulsar(name=pulsar_name, dummy_type=PulsarType.PULSAR_QCM)
        submodules = pulsar.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{pulsar_name}_{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], AWGSequencer) for seq_idx in seq_idxs)
        assert expected_names == registered_names
