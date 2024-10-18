import pytest
from unittest.mock import MagicMock, create_autospec
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.qblox.qblox_sequencer import QbloxSequencer
from qililab.typings import ChannelID, Parameter
from qililab.instruments.instrument import ParameterNotFound
from qililab.typings.instruments import QcmQrm
from qpysequence import Sequence as QpySequence


@pytest.fixture
def qblox_settings():
    return {
        "alias": "qblox_module_1",
        "awg_sequencers": [
            {
                "identifier": 0,
                "outputs": [3, 2],
                "intermediate_frequency": 100e6,
                "gain_imbalance": 0.05,
                "phase_imbalance": 0.02,
                "hardware_modulation": True,
                "gain_i": 1.0,
                "gain_q": 1.0,
                "offset_i": 0.0,
                "offset_q": 0.0,
                "num_bins": 1024
            },
            {
                "identifier": 1,
                "outputs": [1, 0],
                "intermediate_frequency": 50e6,
                "gain_imbalance": 0.0,
                "phase_imbalance": 0.0,
                "hardware_modulation": False,
                "gain_i": 0.5,
                "gain_q": 0.5,
                "offset_i": 0.1,
                "offset_q": 0.1,
                "num_bins": 512
            }
        ],
        "out_offsets": [0.0, 0.1, 0.2, 0.3],
    }

@pytest.fixture
def qblox_module(qblox_settings):
    return QbloxModule(settings=qblox_settings)


class TestQblox:

    def test_qblox_initialization(self, qblox_module, qblox_settings):
        assert qblox_module.alias == "qblox_module_1"
        assert len(qblox_module.awg_sequencers) == 2
        assert qblox_module.out_offsets == qblox_settings["out_offsets"]

    def test_qblox_num_sequencers(self, qblox_module):
        assert qblox_module.num_sequencers == 2

    def test_qblox_get_sequencer(self, qblox_module):
        sequencer = qblox_module.get_sequencer(0)
        assert sequencer.identifier == 0
        assert sequencer.outputs == [3, 2]
        assert sequencer.intermediate_frequency == 100e6
        assert sequencer.gain_imbalance == 0.05
        assert sequencer.phase_imbalance == 0.02
        assert sequencer.hardware_modulation is True
        assert sequencer.gain_i == 1.0
        assert sequencer.gain_q == 1.0
        assert sequencer.offset_i == 0.0
        assert sequencer.offset_q == 0.0
        assert sequencer.num_bins == 1024

        # Test invalid sequencer access
        with pytest.raises(IndexError):
            qblox_module.get_sequencer(10)  # Invalid sequencer ID

    def test_qblox_initial_setup(self, qblox_module):
        qblox_module.device = create_autospec(QcmQrm, instance=True)
        qblox_module.initial_setup()

        # Ensure device setup methods are called correctly
        # assert qblox_module.device.disconnect_outputs.called
        for idx in range(qblox_module.num_sequencers):
            sequencer = qblox_module.get_sequencer(idx)
            qblox_module.device.sequencers[sequencer.identifier].sync_en.assert_called_with(False)

    def test_qblox_upload_qpysequence(self, qblox_module):
        mock_sequence = MagicMock(spec=QpySequence)
        qblox_module.upload_qpysequence(qpysequence=mock_sequence, channel_id=0)

        sequencer = qblox_module.get_sequencer(0)
        qblox_module.device.sequencers[sequencer.identifier].sequence.assert_called_once()

    def test_qblox_set_parameter(self, qblox_module):
        # Test setting a valid parameter
        qblox_module.set_parameter(Parameter.GAIN, value=2.0, channel_id=0)
        sequencer = qblox_module.get_sequencer(0)
        assert sequencer.gain_i == 2.0
        assert sequencer.gain_q == 2.0

        # Test invalid channel ID
        with pytest.raises(Exception):
            qblox_module.set_parameter(Parameter.GAIN, value=2.0, channel_id=5)

        # Test invalid parameter
        with pytest.raises(ParameterNotFound):
            qblox_module.set_parameter(MagicMock(spec=Parameter), value=42, channel_id=0)

    def test_qblox_run(self, qblox_module):
        qblox_module.run(channel_id=0)
        sequencer = qblox_module.get_sequencer(0)
        qblox_module.device.arm_sequencer.assert_called_with(sequencer=sequencer.identifier)
        qblox_module.device.start_sequencer.assert_called_with(sequencer=sequencer.identifier)

    def test_qblox_clear_cache(self, qblox_module):
        qblox_module.cache = {0: MagicMock()}
        qblox_module.clear_cache()
        assert qblox_module.cache == {}
        assert qblox_module.sequences == {}

    def test_qblox_reset(self, qblox_module):
        qblox_module.reset()
        qblox_module.device.reset.assert_called_once()
        assert qblox_module.cache == {}
        assert qblox_module.sequences == {}
