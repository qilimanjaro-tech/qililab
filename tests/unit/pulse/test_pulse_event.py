"""Tests for the Pulse class."""
import numpy as np
import pytest

from qililab.circuit import DRAGPulse, GaussianPulse, SquarePulse
from qililab.pulse import Drag, Gaussian, Pulse, PulseEvent, Rectangular
from qililab.utils import Waveforms


@pytest.fixture(
    name="pulse_event",
    params=[
        Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=Rectangular()),
        Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=Gaussian(num_sigmas=4)),
        Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=Drag(num_sigmas=4, drag_coefficient=2)),
        SquarePulse(amplitude=1, phase=0, duration=50, frequency=1e9),
        GaussianPulse(amplitude=1, phase=0, duration=50, frequency=1e9, sigma=4),
        DRAGPulse(amplitude=1, phase=0, duration=50, frequency=1e9, sigma=4, delta=2),
    ],
)
def fixture_pulse_event(request: pytest.FixtureRequest) -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse = request.param
    return PulseEvent(pulse=pulse, start_time=0)


class TestPulseEvent:
    """Unit tests checking the PulseEvent attributes and methods"""

    def test_modulated_waveforms_method(self, pulse_event: PulseEvent):
        """Test modulated_waveforms method."""
        waveforms = pulse_event.modulated_waveforms()
        assert isinstance(waveforms, Waveforms)

    def test_envelope_method(self, pulse_event: PulseEvent):
        """Test envelope method"""
        envelope = pulse_event.pulse.envelope(amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse_event: PulseEvent):
        """Test to_dict method"""
        dictionary = pulse_event.to_dict()
        assert isinstance(dictionary, dict)

    def test_from_dict_method(self, pulse_event: PulseEvent):
        """Test from_dict method"""
        dictionary = pulse_event.to_dict()
        new_pulse_event = PulseEvent.from_dict(dictionary=dictionary)
        assert isinstance(new_pulse_event, PulseEvent)
        assert new_pulse_event == pulse_event

    def test_end_time(self, pulse_event: PulseEvent):
        """Test end_time property."""
        assert pulse_event.duration == pulse_event.end_time - pulse_event.start_time
