"""File testing the AWG class."""
import pytest
from qpysequence import Sequence as QpySequence

from qililab.instruments import AWG
from qililab.instruments.awg_settings import AWGSequencer
from qililab.pulse import PulseBusSchedule


class DummyAWG(AWG):
    """Dummy AWG class."""

    # pylint: disable=unused-argument
    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list:
        return []

    def run(self):  # pylint: disable=arguments-differ
        pass

    def upload(self, port: str):
        pass

    def upload_qpysequence(self, qpysequence: QpySequence, port: str):
        pass


@pytest.fixture(name="awg")
def fixture_awg():
    """Fixture that returns an instance of a dummy AWG."""
    settings = {
        "alias": "QRM",
        "firmware": "0.7.0",
        "num_sequencers": 2,
        "awg_sequencers": [
            {
                "identifier": 0,
                "chip_port_id": "feedline_input",
                "outputs": [0, 1],
                "intermediate_frequency": 20000000,
                "gain_i": 0.1,
                "gain_q": 0.1,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_i": 0,
                "offset_q": 0,
                "hardware_modulation": True,
            },
            {
                "identifier": 1,
                "chip_port_id": "feedline_output",
                "outputs": [2, 3],
                "intermediate_frequency": 20000000,
                "gain_i": 0.1,
                "gain_q": 0.1,
                "gain_imbalance": 1,
                "phase_imbalance": 0,
                "offset_i": 0,
                "offset_q": 0,
                "hardware_modulation": True,
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
        assert awg.settings.firmware == "0.7.0"
        assert awg.settings.num_sequencers == 2
        for idx, sequencer in enumerate(awg.settings.awg_sequencers):
            assert isinstance(sequencer, AWGSequencer)
            assert sequencer.identifier == idx
            assert sequencer.chip_port_id in {"feedline_input", "feedline_output"}
            assert sequencer.outputs == [0 + 2 * idx, 1 + 2 * idx]
            assert sequencer.intermediate_frequency == 20000000
            assert sequencer.gain_i == 0.1
            assert sequencer.gain_q == 0.1
            assert sequencer.gain_imbalance == 1
            assert sequencer.phase_imbalance == 0
            assert sequencer.offset_i == 0
            assert sequencer.offset_q == 0
            assert sequencer.hardware_modulation is True


class TestProperties:
    """Test properties of the AWG class."""

    def test_num_sequencers_property(self, awg: AWG):
        """Test the num_sequencers property."""
        assert awg.num_sequencers == awg.settings.num_sequencers

    def test_awg_sequencers_property(self, awg: AWG):
        """Test the awg_sequencers property."""
        assert awg.awg_sequencers == awg.settings.awg_sequencers

    def test_intermediate_frequencies_property(self, awg: AWG):
        """Test the intermediate_frequency property."""
        assert awg.intermediate_frequencies == [
            sequencer.intermediate_frequency for sequencer in awg.settings.awg_sequencers
        ]


class TestMethods:
    """Test methods of the AWG class."""

    def test_get_sequencer_raises_error(self, awg: AWG):
        """Test the get_sequencer method raises an error."""
        awg.settings.awg_sequencers[1].identifier = 0
        with pytest.raises(ValueError, match="Each sequencer should have a unique id"):
            awg.get_sequencer(sequencer_id=0)
