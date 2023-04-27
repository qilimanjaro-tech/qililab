"""Tests for the ExponentialCorrection predistortion class."""
import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_predistortion import ExponentialCorrection
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Waveforms

# Parameters of the Pulse
AMPLITUDE = 0.9
PHASE = [0, np.pi / 3, 2 * np.pi, 3 * np.pi]
DURATION = [1, 2, 47]  # TODO: Add 0 to this test?
FREQUENCY = 0.7e9


@pytest.fixture(
    name="predistorted_pulses", params=[Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]
)
def fixture_predistorted_pulses(request: pytest.FixtureRequest) -> list[ExponentialCorrection]:
    """Fixture for the ExponentialCorrection predistortion class."""
    shape = request.param
    predistortions = []

    for phase in PHASE:
        for duration in DURATION:
            pulse = Pulse(amplitude=AMPLITUDE, phase=phase, duration=duration, frequency=FREQUENCY, pulse_shape=shape)
            predistortion = ExponentialCorrection(pulse=pulse, tau_exponential=0.9, amp=0.8)
            predistortion2 = ExponentialCorrection(pulse=pulse, tau_exponential=0.8, amp=-1.2)
            predistortion3 = ExponentialCorrection(pulse=predistortion, tau_exponential=1.3, amp=2.0)
            predistortion4 = ExponentialCorrection(pulse=predistortion3, tau_exponential=0.5, amp=-5.0)

            predistortions.extend([predistortion, predistortion2, predistortion3, predistortion4])

    return predistortions


class TestExponentialCorrection:
    """Unit tests checking the ExponentialCorrection attributes and methods"""

    def test_modulated_waveforms(self, predistorted_pulses: list[ExponentialCorrection]):
        """Test for the modulated_waveforms method."""
        for resolution in [0.1, 1.0]:
            for start_time in [0.0, 0.1]:
                for predistorted_pulse in predistorted_pulses:
                    waveforms = predistorted_pulse.modulated_waveforms(resolution=resolution, start_time=start_time)
                    assert waveforms is not None
                    assert isinstance(waveforms, Waveforms)

    def test_label(self, predistorted_pulses: list[ExponentialCorrection]):
        """Test for the label method."""
        for predistorted_pulse in predistorted_pulses:
            label = predistorted_pulse.label()
            assert isinstance(label, str)
            assert label is not None

    def test_envelope(self, predistorted_pulses: list[ExponentialCorrection]):
        """Test for the envelope method."""
        for predistorted_pulse in predistorted_pulses:
            for resolution in [0.1, 1.0]:
                envelope = predistorted_pulse.envelope(amplitude=AMPLITUDE, resolution=resolution)
                assert envelope is not None
                assert isinstance(envelope, np.ndarray)

    def test_to_dict(self, predistorted_pulses: list[ExponentialCorrection]):
        """Test for the to_dict method."""
        for predistorted_pulse in predistorted_pulses:
            dictionary = predistorted_pulse.to_dict()
            assert dictionary is not None
            assert isinstance(dictionary, dict)
            assert list(dictionary.keys()) == [
                RUNCARD.NAME,
                PulseShapeSettingsName.TAU_EXPONENTIAL.value,
                PulseShapeSettingsName.AMP.value,
            ]
