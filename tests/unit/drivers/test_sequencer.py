"""Tests for the Sequencer class."""
import copy
import pytest
from qililab.drivers.instruments.qblox import Sequencer
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from qpysequence.sequence import Sequence as QpySequence
from tests.data import Galadriel
from unittest.mock import patch


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0)
    return PulseBusSchedule(timeline=[pulse_event], port=0)

class DummySequencer(Sequencer):
    """Dummy Sequencer class for testing"""


@pytest.fixture(name="sequencer")
def fixture_sequencer():
    """Return an instance of Sequencer class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return DummySequencer(settings=settings)


class TestSequencer:
    """Unit tests checking the Sequencer attributes and methods"""

    def test_execute(self, sequencer, pulse_bus_schedule):
        """Test compile method."""
        with patch("qililab.drivers.instruments.QBlox.qcm_qrm.QililabQcmQrm.arm_sequencer") as mock_arm_sequencer:
            with patch("qililab.drivers.instruments.QBlox.qcm_qrm.QililabQcmQrm.start_sequencer") as mock_start_sequencer:
                sequencer.execute(pulse_bus_schedule, nshots=1000, repetition_duration=2000, num_bins=1)
                sequence = sequencer.sequence
                assert isinstance(sequence, QpySequence)
                assert sequence._program.duration == 1000 * 2000 + 4
