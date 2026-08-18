import numpy as np
import pytest

from qililab.pulse_distortion.bias_tee_correction import BiasTeeCorrection
from qililab.pulse_distortion.exponential_decay_correction import ExponentialCorrection
from qililab.pulse_distortion.lfilter_correction import LFilterCorrection
from qililab.pulse_distortion.pulse_distortion import PulseDistortion
from qililab.typings import PulseDistortionName


def test_bias_tee_correction_apply_returns_normalized_copy():
    envelope = np.ones(10, dtype=float)
    distortion = BiasTeeCorrection(tau_bias_tee=0.5, sampling_rate=2.0, auto_norm=True)

    corrected = distortion.apply(envelope)

    assert corrected.shape == envelope.shape
    assert not np.allclose(corrected, envelope)
    assert np.isclose(np.max(np.real(corrected)), np.max(envelope))
    assert distortion.to_dict()["name"] == PulseDistortionName.BIAS_TEE_CORRECTION.value


@pytest.mark.parametrize("amp", [0.25, -0.25])
def test_exponential_correction_branches(amp):
    envelope = np.linspace(0.0, 1.0, 8)
    distortion = ExponentialCorrection(tau_exponential=0.75, amp=amp, sampling_rate=2.0)

    corrected = distortion.apply(envelope)

    assert corrected.shape == envelope.shape
    assert not np.allclose(corrected, envelope)


def test_pulse_distortion_from_dict_rejects_name_mismatch():
    payload = {
        "name": "wrong_name",
        "tau_bias_tee": 0.5,
        "sampling_rate": 2.0,
        "norm_factor": 1.0,
        "auto_norm": True,
    }
    with pytest.raises(ValueError, match="does not match the given dict name"):
        BiasTeeCorrection.from_dict(payload)


def test_pulse_distortion_factory_roundtrip():
    distortion = BiasTeeCorrection(tau_bias_tee=0.5)
    serialized = distortion.to_dict()
    restored = PulseDistortion.from_dict(serialized)
    assert isinstance(restored, BiasTeeCorrection)


@pytest.mark.parametrize(
    "distortion",
    [
        BiasTeeCorrection(tau_bias_tee=50.0),
        ExponentialCorrection(tau_exponential=5.0, amp=0.4),
        ExponentialCorrection(tau_exponential=5.0, amp=-0.4),
        LFilterCorrection(a=[1.0, -0.5], b=[0.6, 0.2]),
    ],
)
def test_apply_equals_filter_when_no_normalization(distortion):
    """`apply` without normalization returns exactly the raw `_filter` output."""
    envelope = np.ones(50, dtype=float)

    assert not distortion.auto_norm
    assert distortion.norm_factor == 1.0
    np.testing.assert_allclose(distortion.apply(envelope), distortion._filter(envelope))


@pytest.mark.parametrize(
    "distortion",
    [
        BiasTeeCorrection(tau_bias_tee=50.0),
        LFilterCorrection(a=[1.0, -0.5], b=[0.6, 0.2]),
    ],
)
def test_amplitude_gain_matches_filter_peak_ratio(distortion):
    """`amplitude_gain` is the peak ratio of the raw filter output to the original envelope."""
    envelope = np.ones(50, dtype=float)

    gain = distortion.amplitude_gain(envelope)
    expected = np.max(np.abs(np.real(distortion._filter(envelope)))) / np.max(np.abs(np.real(envelope)))

    assert gain == pytest.approx(expected)
    assert gain > 1.0  # these filters inflate a unit pulse


@pytest.mark.parametrize(
    "distortion",
    [
        BiasTeeCorrection(tau_bias_tee=50.0),
        LFilterCorrection(a=[1.0, -0.5], b=[0.6, 0.2]),
    ],
)
def test_auto_norm_divides_by_amplitude_gain(distortion):
    """With `auto_norm`, the played waveform is the raw filter output divided by `amplitude_gain`."""
    envelope = np.ones(50, dtype=float)

    gain = distortion.amplitude_gain(envelope)
    normalized = type(distortion).from_dict({**distortion.to_dict(), "auto_norm": True}).apply(envelope)

    np.testing.assert_allclose(normalized, distortion._filter(envelope) / gain)
    assert np.max(np.abs(np.real(normalized))) == pytest.approx(np.max(np.abs(np.real(envelope))))


def test_amplitude_gain_defaults_to_one_for_zero_envelope():
    """A zero (or real-part-less) envelope has no defined gain, so it defaults to 1.0."""
    assert BiasTeeCorrection(tau_bias_tee=50.0).amplitude_gain(np.zeros(10)) == 1.0
