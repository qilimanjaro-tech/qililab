""" Test StreamArray """
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from h5py import Dataset
import qililab as ql

from qililab.result import StreamArray

AMP_VALUES = np.arange(0, 1, 2)

@pytest.fixture(name="stream_array")
def fixture_stream_array():
    """fixture_stream_array

    Returns:
        stream_array: StreamArray
    """
    shape = (2, 2)
    path = "test_stream_array.hdf5"
    loops = {"test_amp_loop": AMP_VALUES}

    return StreamArray(shape=shape, path=path, loops=loops)

class TestStreamArray:
    """Test `StreamArray` functionalities."""

    def test_stream_array_instantiation(self, stream_array: StreamArray):
        """Tests the instantiation of a StreamArray object."""
        assert stream_array.results.shape == (2, 2)
        assert (stream_array.results == np.empty(shape=(2, 2))).all
        assert stream_array.path == "test_stream_array.hdf5"
        assert stream_array.loops == {"test_amp_loop": np.arange(0, 1, 2)}

    @patch('qililab.result.stream_results.h5py')
    def test_context_manager(self, mock_h5py: MagicMock, stream_array: StreamArray):
        """Tests context manager real time saving."""

        # test adding outside the context manager
        stream_array[0, 0] = -2
        
        assert stream_array.dataset is None

        # test adding inside the context manager
        with stream_array:
            stream_array[0][0] = 1
            stream_array[0][1] = 2
            stream_array[1][0] = 3
            stream_array[1][1] = 4

        assert (stream_array.results == [[1, 2], [3, 4]]).all
        assert stream_array.dataset is not None
