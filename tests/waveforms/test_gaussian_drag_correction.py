import numpy as np
import pytest

from qililab.core.variables import Domain, FloatVariable, IntVariable
from qililab.waveforms import Gaussian
from qililab.waveforms.gaussian_drag_correction import GaussianDragCorrection


@pytest.fixture(name="gaussian_drag_correction")
def fixture_gaussian_drag_correction():
    return GaussianDragCorrection(1.0, 100, 0.5, 2.5)


class TestGaussianDragCorrection:
    def test_init(self, gaussian_drag_correction: GaussianDragCorrection):
        # test init method
        assert gaussian_drag_correction.amplitude == 1.0
        assert gaussian_drag_correction.duration == 100
        assert gaussian_drag_correction.num_sigmas == 0.5
        assert gaussian_drag_correction.drag_coefficient == 2.5

    def test_envelope_matches_drag_formula(
        self, gaussian_drag_correction: GaussianDragCorrection
    ):
        resolution = 5
        sigma = gaussian_drag_correction.duration / gaussian_drag_correction.num_sigmas
        mu = gaussian_drag_correction.duration / 2
        x = np.arange(gaussian_drag_correction.duration / resolution) * resolution

        base_gaussian = Gaussian(
            amplitude=gaussian_drag_correction.amplitude,
            duration=gaussian_drag_correction.duration,
            num_sigmas=gaussian_drag_correction.num_sigmas,
        ).envelope(resolution=resolution)

        expected = (
            -gaussian_drag_correction.drag_coefficient * (x - mu) / sigma**2
        ) * base_gaussian

        np.testing.assert_allclose(
            gaussian_drag_correction.envelope(resolution=resolution), expected
        )

    def test_get_duration(self, gaussian_drag_correction: GaussianDragCorrection):
        assert gaussian_drag_correction.get_duration() == gaussian_drag_correction.duration

    def test_invalid_amplitude_domain_raises(self):
        bad_amplitude = FloatVariable("amp", Domain.Flux)

        with pytest.raises(ValueError, match="Expected domain Domain.Voltage for amplitude"):
            GaussianDragCorrection(
                amplitude=bad_amplitude,
                duration=100,
                num_sigmas=0.5,
                drag_coefficient=1.0,
            )

    def test_valid_variable_domains(self):
        amplitude = FloatVariable("amp", Domain.Voltage)
        duration = IntVariable("dur", Domain.Time)
        num_sigmas = FloatVariable("sigma", Domain.Scalar)
        drag_coeff = FloatVariable("drag", Domain.Scalar)

        waveform = GaussianDragCorrection(
            amplitude=amplitude,
            duration=duration,
            num_sigmas=num_sigmas,
            drag_coefficient=drag_coeff,
        )

        assert waveform.drag_coefficient == drag_coeff
