import numpy as np
import pytest

from qililab.pulse_distortion.bias_tee_correction import BiasTeeCorrection
from qililab.pulse_distortion.exponential_decay_correction import ExponentialCorrection
from qililab.pulse_distortion.pulse_distortion import PulseDistortion
from qililab.typings import PulseDistortionName


def test_bias_tee_correction_apply_returns_normalized_copy():
    envelope = np.ones(10, dtype=float)
    distortion = BiasTeeCorrection(tau_bias_tee=0.5, sampling_rate=2.0)

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
