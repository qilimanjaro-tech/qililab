"""Tests for the BiasTeeCorrection predistortion class."""
import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_predistortion import BiasTeeCorrection
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
def fixture_predistorted_pulses(request: pytest.FixtureRequest) -> list[BiasTeeCorrection]:
    """Fixture for the BiasTeeCorrection predistortion class."""
    shape = request.param
    predistortions = []

    for phase in PHASE:
        for duration in DURATION:
            pulse = Pulse(amplitude=AMPLITUDE, phase=phase, duration=duration, frequency=FREQUENCY, pulse_shape=shape)
            predistortion = BiasTeeCorrection(pulse=pulse, tau_bias_tee=0.9)
            predistortion2 = BiasTeeCorrection(pulse=predistortion, tau_bias_tee=1.9)
            predistortion3 = BiasTeeCorrection(pulse=predistortion2, tau_bias_tee=0.5)

            predistortions.extend([predistortion, predistortion2, predistortion3])

    return predistortions


class TestBiasTeeCorrection:
    """Unit tests checking the BiasTeeCorrection attributes and methods"""

    def test_modulated_waveforms(self, predistorted_pulses: list[BiasTeeCorrection]):
        """Test for the modulated_waveforms method."""
        for resolution in [0.1, 1.0]:
            for start_time in [0.0, 0.1]:
                for predistorted_pulse in predistorted_pulses:
                    waveforms = predistorted_pulse.modulated_waveforms(resolution=resolution, start_time=start_time)
                    assert waveforms is not None
                    assert isinstance(waveforms, Waveforms)

    def test_label(self, predistorted_pulses: list[BiasTeeCorrection]):
        """Test for the label method."""
        for predistorted_pulse in predistorted_pulses:
            label = predistorted_pulse.label()
            assert isinstance(label, str)
            assert label is not None

    def test_envelope(self, predistorted_pulses: list[BiasTeeCorrection]):
        """Test for the envelope method."""
        for predistorted_pulse in predistorted_pulses:
            for resolution in [0.1, 1.0]:
                envelope = predistorted_pulse.envelope(amplitude=AMPLITUDE, resolution=resolution)
                assert envelope is not None
                assert isinstance(envelope, np.ndarray)

    def test_to_dict(self, predistorted_pulses: list[BiasTeeCorrection]):
        """Test for the to_dict method."""
        for predistorted_pulse in predistorted_pulses:
            dictionary = predistorted_pulse.to_dict()
            assert dictionary is not None
            assert isinstance(dictionary, dict)
            assert list(dictionary.keys()) == [
                RUNCARD.NAME,
                PulseShapeSettingsName.TAU_BIAS_TEE.value,
            ]
