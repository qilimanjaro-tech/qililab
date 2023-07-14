import re

import numpy as np
import pytest

from qililab.waveforms import Arbitrary

samples = np.array(
    [
        0.64534116,
        0.61077185,
        0.84978029,
        0.71466369,
        0.65842367,
        0.77841013,
        0.85828779,
        0.20028723,
        0.45814018,
        0.45901151,
    ]
)


@pytest.fixture(name="arbitrary")
def fixture_square():
    return Arbitrary(samples=samples, duration=1)


class TestArbitrary:
    def test_init(self, arbitrary):
        # test init method
        assert np.allclose(arbitrary.samples, samples)
        assert arbitrary.duration == 1

    def test_envelope(self, arbitrary):
        # test envelope method
        assert np.allclose(arbitrary.envelope(resolution=0.1), samples)

    def test_raise_resolution_duration_error(self, arbitrary):
        error_string = "Duration / resolution does not correspond to len(samples): 1 / 2 != 10"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            arbitrary.envelope(resolution=2)
