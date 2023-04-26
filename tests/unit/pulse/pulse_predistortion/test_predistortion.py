"""Tests for the PulseShape class."""
import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.pulse import Pulse
from qililab.pulse.pulse_predistortion import BiasTeeCorrection, ExponentialCorrection, PredistortedPulse
from qililab.pulse.pulse_shape import Drag, Gaussian, Rectangular
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Waveforms

duration = 50
amplitude = 1.0

list_shapes = [Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]
params = []
for shape in list_shapes:
    pulse = Pulse(amplitude=amplitude, phase=0.0, duration=duration, frequency=1.0, pulse_shape=shape)
    params.extend(
        [
            BiasTeeCorrection(pulse=pulse, tau_bias_tee=1.0),
            ExponentialCorrection(pulse=pulse, tau_exponential=1.0, amp=1.0),
        ]
    )


@pytest.fixture(name="predistorted_pulse", params=params)
def fixture_predistorted_pulse(request: pytest.FixtureRequest) -> PredistortedPulse:
    """Fixture for the PredistortedPulse class."""
    return request.param  # type: ignore


class TestPredistortedPulse:
    """Unit tests checking the PredistortedPulse attributes and methods"""

    def test_modulated_waveforms(self, predistorted_pulse: PredistortedPulse):
        """Test that modulated_waveforms returns a non-empty result"""
        waveforms = predistorted_pulse.modulated_waveforms(resolution=0.1, start_time=0.0)
        assert waveforms is not None

    def test_modulated_waveforms_type(self, predistorted_pulse: PredistortedPulse):
        """Test that modulated_waveforms returns a non-empty result"""
        waveforms = predistorted_pulse.modulated_waveforms(resolution=0.1, start_time=0.0)
        assert isinstance(waveforms, Waveforms)

    def test_label_no_null(self, predistorted_pulse: PredistortedPulse):
        """Test that label returns a non-empty result"""
        label = predistorted_pulse.label()
        assert label is not None

    def test_label_type(self, predistorted_pulse: PredistortedPulse):
        """Test that label returns the expected type"""
        label = predistorted_pulse.label()
        assert isinstance(label, str)

    def test_envelope_no_null(self, predistorted_pulse: PredistortedPulse):
        """Test that envelope returns a non-empty result"""
        envelope = predistorted_pulse.envelope(amplitude=amplitude, resolution=0.1)
        assert envelope is not None

    def test_envelope_type(self, predistorted_pulse: PredistortedPulse):
        """Test that envelope method returns the expected type"""
        envelope = predistorted_pulse.envelope(amplitude=amplitude, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_no_null(self, predistorted_pulse: PredistortedPulse):
        """Test that to_dict returns a non-empty result"""
        result = predistorted_pulse.to_dict()
        assert result is not None

    def test_to_dict_type(self, predistorted_pulse: PredistortedPulse):
        """Test that to_dict method returns the expected type"""
        dictionary = predistorted_pulse.to_dict()
        assert isinstance(dictionary, dict)

    def test_to_dict_result(self, predistorted_pulse: PredistortedPulse):
        """Test that to_dict method returns the expected type"""
        dictionary = predistorted_pulse.to_dict()
        assert list(dictionary.keys()) in [
            [
                RUNCARD.NAME,
                PulseShapeSettingsName.TAU_EXPONENTIAL.value,
                PulseShapeSettingsName.AMP.value,
            ],
            [RUNCARD.NAME, PulseShapeSettingsName.TAU_BIAS_TEE.value],
        ]
