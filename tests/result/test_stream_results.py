"""Test StreamArray"""

import copy
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from tests.data import Galadriel

import qililab as ql
from qililab.result.stream_results import StreamArray

AMP_VALUES = np.arange(0, 1, 2)


@pytest.fixture(name="stream_array")
def fixture_stream_array():
    """fixture_stream_array

    Returns:
        stream_array: StreamArray
    """
    shape = (2, 2)
    loops = {"test_amp_loop": AMP_VALUES}
    platform = ql.build_platform(runcard=copy.deepcopy(Galadriel.runcard))
    experiment_name = "test_stream_array"
    mock_database = MagicMock()
    db_manager = mock_database
    base_path = "base_path"

    return StreamArray(
        shape=shape, loops=loops, platform=platform, experiment_name=experiment_name, db_manager=db_manager, base_path=base_path
    )


class MockGroup:
    """Mock a h5py group."""

    def create_dataset(self, name: str, data: np.ndarray):
        """Creates a dataset"""
        return {}


class MockFile:
    """Mocks a h5py file."""

    def __init__(self):
        """Initialize a mock file."""
        self.dataset = None

    def create_group(self, name: str):
        return MockGroup()

    def create_dataset(self, _: str, data: np.ndarray):
        """Creates a dataset"""
        return copy.deepcopy(data)

    def __exit__(self, *_):
        """mocks exit"""


class TestStreamArray:
    """Test `StreamArray` functionalities."""

    def test_stream_array_instantiation(self, stream_array: StreamArray):
        """Tests the instantiation of a StreamArray object."""
        assert stream_array.results.shape == (2, 2)
        assert (stream_array.results == np.empty(shape=(2, 2))).all
        assert stream_array.loops == {"test_amp_loop": np.arange(0, 1, 2)}

    @patch("h5py.File", return_value=MockFile())
    def test_context_manager(self, mock_h5py: MockFile, stream_array: StreamArray):
        """Tests context manager real time saving."""
        # test adding outside the context manager
        stream_array[0, 0] = -2

        # test adding inside the context manager
        with stream_array:
            stream_array[0, 0] = 1
            stream_array[0, 1] = 2
            stream_array[1, 0] = 3
            stream_array[1, 1] = 4

        assert (stream_array.results == [[1, 2], [3, 4]]).all

        assert len(stream_array) == 2
        assert sum(1 for _ in iter(stream_array)) == 2
        assert str(stream_array) == "[[1. 2.]\n [3. 4.]]"

        assert [1, 2] in stream_array
        assert (stream_array[0] == [1, 2]).all
