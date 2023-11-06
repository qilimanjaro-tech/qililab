""" Test StreamArray """

import numpy as np
import pytest

from qililab.result import StreamArray


@pytest.fixture(name="stream_array")
def fixture_stream_array():
    """fixture_stream_array

    Returns:
        stream_array: StreamArray
    """
    AMP_VALUES = np.arange(0, 1, 2)
    shape = (2, 2)
    path = "test_stream_array"
    loops = {"test_amp_loop": AMP_VALUES}

    return StreamArray(shape=shape, path=path, loops=loops)


class TestStreamArray:
    """Test `StreamArray` functionalities."""

    def test_stream_array_instantiation(self, stream_array: StreamArray):
        """Tests the instantiation of a StreamArray object.

        Args:
            stream_array (StreamArray): StreamArray instance.
        """
        assert stream_array.results.shape == (2, 2)
        assert (stream_array.results == np.empty(shape=(2, 2))).all
        assert stream_array.path == "test_stream_array"
        assert stream_array.loops == {"test_amp_loop": np.arange(0, 1, 2)}
