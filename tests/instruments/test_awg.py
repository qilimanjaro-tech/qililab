"""File testing the AWG class."""
import re

import pytest
from qpysequence import Sequence as QpySequence

from qililab.instruments.awg import AWG
from qililab.instruments.awg_settings import AWGSequencer
from qililab.pulse import PulseBusSchedule


class DummyAWG(AWG):
    """Dummy AWG class."""

    # pylint: disable=unused-argument
    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list:
        return []

    def initial_setup(self):
        pass

    def run(self):  # pylint: disable=arguments-differ
        pass

    def upload(self, channel_id: int | str | None):
        pass

    def upload_qpysequence(self, qpysequence: QpySequence, channel_id: int | str | None):
        pass

    def turn_on(self):
        pass

    def reset(self):
        pass

    def turn_off(self):
        pass


@pytest.fixture(name="awg_settings")
def fixture_awg_settings():
    """Fixture that returns AWG settings."""
    return {
        "alias": "QRM",
        "awg_sequencers": [
            {
                "identifier": 0,
                "output_i": 0,
                "output_q": 1,
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
                "output_i": 2,
                "output_q": 3,
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


@pytest.fixture(name="awg")
def fixture_awg(awg_settings: dict):
    """Fixture that returns an instance of a dummy AWG."""
    return DummyAWG(settings=awg_settings)  # pylint: disable=abstract-class-instantiated


class TestInitialization:
    """Unit tests for the initialization of the AWG class."""

    def test_init(self, awg: AWG):
        """Test the initialization of the AWG class."""
        assert isinstance(awg.settings, AWG.AWGSettings)
        assert awg.settings.alias == "QRM"
        assert awg.num_sequencers == 2
        for idx, sequencer in enumerate(awg.settings.awg_sequencers):
            assert isinstance(sequencer, AWGSequencer)
            assert sequencer.identifier == idx
            assert sequencer.output_i == 0 + 2 * idx
            assert sequencer.output_q == 1 + 2 * idx
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
        assert awg.num_sequencers == len(awg.settings.awg_sequencers)

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

    def test_num_sequencers_error(self, awg_settings: dict):
        """test that an error is raised if more than _NUM_MAX_SEQUENCERS are in the qblox module"""

        awg_settings["awg_sequencers"] = []
        error_string = re.escape("The number of sequencers must be greater than 0. Received: 0")
        with pytest.raises(ValueError, match=error_string):
            DummyAWG(settings=awg_settings)  # pylint: disable=abstract-class-instantiated
