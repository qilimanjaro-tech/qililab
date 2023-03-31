"""File testing the AWG class."""
import pytest

from qililab.instruments import AWG
from qililab.instruments.awg_settings import AWGIQChannel, AWGOutputChannel, AWGSequencer, AWGSequencerPath
from qililab.pulse import PulseBusSchedule
from qililab.typings import Category


class DummyAWG(AWG):
    """Dummy AWG class."""

    def compile(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int) -> list:
        return []

    def run(self):
        pass


@pytest.fixture(name="awg")
def fixture_awg():
    """Fixture that returns an instance of a dummy AWG."""
    settings = {
        "alias": "QRM",
        "id_": 0,
        "category": "awg",
        "firmware": "0.7.0",
        "num_sequencers": 2,
        "awg_sequencers": [
            {
                "identifier": 0,
                "chip_port_id": 100,
                "path0": {"output_channel": 0},
                "path1": {"output_channel": 1},
                "intermediate_frequency": 20000000,
                "gain_path0": 0.1,
                "gain_path1": 0.1,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_path0": 0,
                "offset_path1": 0,
                "hardware_modulation": True,
            },
            {
                "identifier": 1,
                "chip_port_id": 101,
                "path0": {"output_channel": 2},
                "path1": {"output_channel": 3},
                "intermediate_frequency": 20000000,
                "gain_path0": 0.1,
                "gain_path1": 0.1,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_path0": 0,
                "offset_path1": 0,
                "hardware_modulation": True,
            },
        ],
        "awg_iq_channels": [
            {
                "identifier": 0,
                "i_channel": {"awg_sequencer_identifier": 0, "awg_sequencer_path_identifier": 0},
                "q_channel": {"awg_sequencer_identifier": 0, "awg_sequencer_path_identifier": 1},
            },
            {
                "identifier": 1,
                "i_channel": {"awg_sequencer_identifier": 1, "awg_sequencer_path_identifier": 1},
                "q_channel": {"awg_sequencer_identifier": 1, "awg_sequencer_path_identifier": 0},
            },
        ],
    }
    return DummyAWG(settings=settings)  # pylint: disable=abstract-class-instantiated


class TestInitialization:
    """Unit tests for the initialization of the AWG class."""

    def test_init(self, awg: AWG):
        """Test the initialization of the AWG class."""
        assert isinstance(awg.settings, AWG.AWGSettings)
        assert awg.settings.alias == "QRM"
        assert awg.settings.id_ == 0
        assert isinstance(awg.settings.category, Category)
        assert awg.settings.category == Category.AWG
        assert awg.settings.firmware == "0.7.0"
        assert awg.settings.num_sequencers == 1
        assert isinstance(awg.settings.awg_sequencers[0], AWGSequencer)
        assert awg.settings.awg_sequencers[0].identifier == 0
        assert awg.settings.awg_sequencers[0].chip_port_id == 100
        assert isinstance(awg.settings.awg_sequencers[0].path0, AWGSequencerPath)
        assert isinstance(awg.settings.awg_sequencers[0].path1.output_channel, AWGOutputChannel)
        assert awg.settings.awg_sequencers[0].path0.output_channel.identifier == 0
        assert awg.settings.awg_sequencers[0].path1.output_channel.identifier == 1
        assert awg.settings.awg_sequencers[0].intermediate_frequency == 20000000
        assert awg.settings.awg_sequencers[0].gain_path0 == 0.1
        assert awg.settings.awg_sequencers[0].gain_path1 == 0.1
        assert awg.settings.awg_sequencers[0].gain_imbalance == 1
        assert awg.settings.awg_sequencers[0].phase_imbalance == 0
        assert awg.settings.awg_sequencers[0].offset_path0 == 0
        assert awg.settings.awg_sequencers[0].offset_path1 == 0
        assert awg.settings.awg_sequencers[0].hardware_modulation is True
        assert isinstance(awg.settings.awg_iq_channels[0], AWGIQChannel)
        assert awg.settings.awg_iq_channels[0].identifier == 0
        assert awg.settings.awg_iq_channels[0].i_channel.awg_sequencer_identifier == 0
        assert awg.settings.awg_iq_channels[0].i_channel.awg_sequencer_path_identifier.value == 0
        assert awg.settings.awg_iq_channels[0].q_channel.awg_sequencer_identifier == 0
        assert awg.settings.awg_iq_channels[0].q_channel.awg_sequencer_path_identifier.value == 1


class TestProperties:
    """Test properties of the AWG class."""

    def test_num_sequencers_property(self, awg: AWG):
        """Test the num_sequencers property."""
        assert awg.num_sequencers == awg.settings.num_sequencers

    def test_awg_sequencers_property(self, awg: AWG):
        """Test the awg_sequencers property."""
        assert awg.awg_sequencers == awg.settings.awg_sequencers

    def test_awg_iq_channels_property(self, awg: AWG):
        """Test the awg_iq_channels property."""
        assert awg.awg_iq_channels == awg.settings.awg_iq_channels

    def test_intermediate_frequencies_property(self, awg: AWG):
        """Test the intermediate_frequency property."""
        assert awg.intermediate_frequencies == [
            sequencer.intermediate_frequency for sequencer in awg.settings.awg_sequencers
        ]


class TestMethods:
    """Test methods of the AWG class."""

    def test_offset_i(self, awg: AWG):
        """Test the offset_i method."""
        offset_i = awg.offset_i(sequencer_id=0)
        assert offset_i == awg.settings.awg_sequencers[0].offset_path0
        offset_i = awg.offset_i(sequencer_id=1)
        assert offset_i == awg.settings.awg_sequencers[1].offset_path1

    def test_offset_q(self, awg: AWG):
        """Test the offset_q method."""
        offset_q = awg.offset_q(sequencer_id=0)
        assert offset_q == awg.settings.awg_sequencers[0].offset_path1
        offset_q = awg.offset_q(sequencer_id=1)
        assert offset_q == awg.settings.awg_sequencers[1].offset_path0

    def test_get_sequencer_path_id_mapped_to_i_channel_raises_error(self, awg: AWG):
        """Test the get_sequencer_path_id_mapped_to_i_channel method raises an error."""
        awg.settings.awg_iq_channels[1].i_channel.awg_sequencer_identifier = 0
        with pytest.raises(ValueError, match="Each sequencer should only contain 1 path connected to the I channel."):
            awg.get_sequencer_path_id_mapped_to_i_channel(sequencer_id=0)

    def test_get_sequencer_path_id_mapped_to_q_channel_raises_error(self, awg: AWG):
        """Test the get_sequencer_path_id_mapped_to_q_channel method raises an error."""
        awg.settings.awg_iq_channels[1].q_channel.awg_sequencer_identifier = 0
        with pytest.raises(ValueError, match="Each sequencer should only contain 1 path connected to the Q channel."):
            awg.get_sequencer_path_id_mapped_to_q_channel(sequencer_id=0)

    def test_get_sequencer_raises_error(self, awg: AWG):
        """Test the get_sequencer method raises an error."""
        awg.settings.awg_sequencers[1].identifier = 0
        with pytest.raises(ValueError, match="Each sequencer should have a unique id"):
            awg.get_sequencer(sequencer_id=0)
