"""module to test the pulsar class."""
from qblox_instruments.types import PulsarType
from qcodes import Instrument

from qililab.drivers.instruments.qblox.pulsar import Pulsar
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM

NUM_SUBMODULES = 6
PULSAR_NAME = "test"


class TestPulsar:
    """Unit tests checking the QililabPulsar attributes and methods"""

    @classmethod
    def teardown_method(cls):
        """Tear down after all tests have been run"""
        Instrument.close_all()

    def test_init_qcm_type(self):
        """Unittest for init method for a QCM pulsar."""
        pulsar = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QCM)
        sequencers_prefix = "sequencer"
        submodules = pulsar.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{PULSAR_NAME}_{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], SequencerQCM) for seq_idx in seq_idxs)
        assert expected_names == registered_names

    def test_init_qrm_type(self):
        """Unittest for init method for a QRM pulsar."""
        pulsar = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QRM)
        sequencers_prefix = "sequencer"
        submodules = pulsar.submodules
        seq_idxs = list(submodules.keys())
        expected_names = [f"{PULSAR_NAME}_{sequencers_prefix}{idx}" for idx in range(6)]
        registered_names = [submodules[seq_idx].name for seq_idx in seq_idxs]

        assert len(submodules) == NUM_SUBMODULES
        assert all(isinstance(submodules[seq_idx], SequencerQRM) for seq_idx in seq_idxs)
        assert expected_names == registered_names

    def test_params(self):
        """Unittest to test the params property."""
        pulsar_qcm = Pulsar(alias=f"{PULSAR_NAME}1", dummy_type=PulsarType.PULSAR_QCM)
        pulsar_qrm = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QRM)

        assert pulsar_qcm.params == pulsar_qcm.parameters
        assert pulsar_qrm.params == pulsar_qrm.parameters

    def test_alias(self):
        """Unittest to test the alias property."""
        pulsar_qcm = Pulsar(alias=f"{PULSAR_NAME}1", dummy_type=PulsarType.PULSAR_QCM)
        pulsar_qrm = Pulsar(alias=PULSAR_NAME, dummy_type=PulsarType.PULSAR_QRM)

        assert pulsar_qcm.alias == pulsar_qcm.name
        assert pulsar_qrm.alias == pulsar_qrm.name
