""" Test StreamArray """
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab.result import StreamArray

AMP_VALUES = np.arange(0, 1, 2)

class MockStreamArray(StreamArray):
    """Mocks the stream array functionality."""

    def __init__(self, shape, path, loops):
        super().__init__(shape, path, loops)

    def __setitem__(self, key, value):
        """Mocks the set item functionality."""
        self.results[key] = value
        
    def __enter__(self):
        """Enters the context manager."""

        
@pytest.fixture(name="stream_array")
def fixture_stream_array():
    """fixture_stream_array

    Returns:
        stream_array: StreamArray
    """
    shape = (2, 2)
    path = "test_stream_array.hdf5"
    loops = {"test_amp_loop": AMP_VALUES}

    return MockStreamArray(shape=shape, path=path, loops=loops)


class TestStreamArray:
    """Test `StreamArray` functionalities."""

    def test_stream_array_instantiation(self, stream_array: MockStreamArray):
        """Tests the instantiation of a StreamArray object."""
        assert stream_array.results.shape == (2, 2)
        assert (stream_array.results == np.empty(shape=(2, 2))).all
        assert stream_array.path == "test_stream_array.hdf5"
        assert stream_array.loops == {"test_amp_loop": np.arange(0, 1, 2)}

    def test_context_manager(self, stream_array: MockStreamArray):
        """Tests context manager real time saving."""
        
        # test that adding outside the context manager does not modify the stream array
        stream_array[0, 0] = -2 
        
        assert (stream_array.results == np.empty(shape=(2, 2))).all
        
        # test that adding inside the context manager modifies the stream array
        with stream_array:
            stream_array[0][0] = 1
            stream_array[0][1] = 2
            stream_array[1][0] = 3
            stream_array[1][1] = 4
        
        assert (stream_array.results == [[1, 2], [3, 4]]).all
        
        # test that file attribute is None and dataset object is empty 
        assert stream_array.file is None
        assert stream_array.dataset is None
