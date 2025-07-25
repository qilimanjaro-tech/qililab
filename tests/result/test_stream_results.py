"""Test StreamArray"""

import copy
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from tests.data import Galadriel

from qililab.data_management import build_platform
from qililab.result import stream_results
from qililab.result.stream_results import RawStreamArray, StreamArray
from qililab.typings.enums import Parameter

AMP_VALUES = np.arange(0, 1, 2)


@pytest.fixture(name="stream_array")
def fixture_stream_array():
    """fixture_stream_array

    Returns:
        stream_array: StreamArray
    """
    shape = (2, 2, 1)
    loops = {"test_amp_loop": AMP_VALUES}
    platform = build_platform(runcard=copy.deepcopy(Galadriel.runcard))
    experiment_name = "test_stream_array"
    base_path = "base_path"
    mock_database = MagicMock()
    db_manager = mock_database

    return StreamArray(
        shape=shape,
        loops=loops,
        platform=platform,
        experiment_name=experiment_name,
        db_manager=db_manager,
        base_path=base_path,
    )


@pytest.fixture(name="stream_array_dict_loops")
def fixture_stream_array_dict_loops():
    """fixture_stream_array

    Returns:
        stream_array: StreamArray
    """
    shape = (2, 2, 1)
    loops = {"test_amp_loop": {"bus": "readout", "units": "V", "parameter": Parameter.VOLTAGE, "array": AMP_VALUES}}
    platform = build_platform(runcard=copy.deepcopy(Galadriel.runcard))
    experiment_name = "test_stream_array"
    base_path = "base_path"
    mock_database = MagicMock()
    db_manager = mock_database

    return StreamArray(
        shape=shape,
        loops=loops,
        platform=platform,
        experiment_name=experiment_name,
        db_manager=db_manager,
        base_path=base_path,
    )


@pytest.fixture(name="stream_results")
def fixture_stream_results():
    """fixture_stream_results
    Returns:
        stream_results: RawStreamArray
    """
    shape = (2, 2, 1)
    path = "test_stream_array.hdf5"
    loops = {"test_amp_loop": AMP_VALUES}

    return stream_results(shape=shape, path=path, loops=loops)


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

    def create_group(self, name: str, track_order: bool = False):
        return MockGroup()

    def create_dataset(self, _: str, data: np.ndarray, dtype=None):
        """Creates a dataset"""
        return copy.deepcopy(data)

    def __exit__(self, *_):
        """mocks exit"""


class TestStreamArray:
    """Test `StreamArray` functionalities."""

    def test_stream_array_instantiation(self, stream_array: StreamArray):
        """Tests the instantiation of a StreamArray object."""
        assert stream_array.loops == {"test_amp_loop": np.arange(0, 1, 2)}

    def test_stream_array_with_loop_dict(self, stream_array_dict_loops: StreamArray):
        """Tests the instantiation of a StreamArray object."""
        assert stream_array_dict_loops.loops == {
            "test_amp_loop": {
                "bus": "readout",
                "units": "V",
                "parameter": Parameter.VOLTAGE,
                "array": np.arange(0, 1, 2),
            }
        }

    @patch("h5py.File", return_value=MockFile(), autospec=False)
    def test_context_manager(self, mock_h5py: MockFile, stream_array: StreamArray):
        """Tests context manager real time saving."""
        # test adding outside the context manager
        stream_array[0, 0] = [-2]

        # test adding inside the context manager
        with stream_array:
            stream_array[0, 0] = [1]
            stream_array[0, 1] = [2]
            stream_array[1, 0] = [3]
            stream_array[1, 1] = [4]

        assert (stream_array.results == [[1, 2], [3, 4]]).all

        assert len(stream_array) == 2
        assert sum(1 for _ in iter(stream_array)) == 2
        assert str(stream_array) == "[[[1.]\n  [2.]]\n\n [[3.]\n  [4.]]]"

        assert [1, 2] in stream_array
        assert (stream_array[0] == [1, 2]).all

    @patch("h5py.File", return_value=MockFile(), autospec=False)
    def test_context_manager_complex_values(self, mock_h5py: MockFile, stream_array: StreamArray):
        """Tests context manager real time saving."""
        # test adding outside the context manager
        stream_array[0, 0] = [np.complex128(-2 + 1j)]

        # test adding inside the context manager
        with stream_array:
            stream_array[0, 0] = [np.complex128(1 + 1j)]
            stream_array[0, 1] = [np.complex128(2 + 2j)]
            stream_array[1, 0] = [np.complex128(3 + 3j)]
            stream_array[1, 1] = [np.complex128(4 + 4j)]

        assert (stream_array.results == [[1, 2], [3, 4]]).all

        assert len(stream_array) == 2
        assert sum(1 for _ in iter(stream_array)) == 2
        assert str(stream_array) == "[[[1.+1.j]\n  [2.+2.j]]\n\n [[3.+3.j]\n  [4.+4.j]]]"

        assert [1.0 + 1.0j, 2.0 + 2.0j] in stream_array
        assert (stream_array[0] == [1.0 + 1.0j, 2.0 + 2.0j]).all


class TestRawStreamArray:
    """Test `StreamArray` functionalities."""

    def test_stream_array_instantiation(self, stream_results: RawStreamArray):
        """Tests the instantiation of a StreamArray object."""
        assert stream_results.path == "test_stream_array.hdf5"
        assert stream_results.loops == {"test_amp_loop": np.arange(0, 1, 2)}

    @patch("h5py.File", return_value=MockFile(), autospec=False)
    def test_context_manager(self, mock_h5py: MockFile, stream_results: RawStreamArray):
        """Tests context manager real time saving."""
        # test adding outside the context manager
        stream_results[0, 0] = [-2]

        assert stream_results._dataset is None

        # test adding inside the context manager
        with stream_results:
            stream_results[0, 0] = [1]
            stream_results[0, 1] = [2]
            stream_results[1, 0] = [3]
            stream_results[1, 1] = [4]

        assert (stream_results.results == [[1, 2], [3, 4]]).all
        assert stream_results._dataset is not None
        assert (stream_results._dataset == [[1, 2], [3, 4]]).all
        assert stream_results._dataset[0, 0] == 1

        assert len(stream_results) == 2
        assert sum(1 for _ in iter(stream_results)) == 2
        assert str(stream_results) == "[[[1.]\n  [2.]]\n\n [[3.]\n  [4.]]]"
        assert (stream_results[0] == [1, 2]).all

    @patch("h5py.File", return_value=MockFile(), autospec=False)
    def test_context_manager_complex_values(self, mock_h5py: MockFile, stream_results: RawStreamArray):
        """Tests context manager real time saving."""
        # test adding outside the context manager
        stream_results[0, 0] = [np.complex128(-2 + 1j)]

        # test adding inside the context manager
        with stream_results:
            stream_results[0, 0] = [np.complex128(1 + 1j)]
            stream_results[0, 1] = [np.complex128(2 + 2j)]
            stream_results[1, 0] = [np.complex128(3 + 3j)]
            stream_results[1, 1] = [np.complex128(4 + 4j)]

        assert (stream_results.results == [[1, 2], [3, 4]]).all

        assert len(stream_results) == 2
        assert sum(1 for _ in iter(stream_results)) == 2
        assert str(stream_results) == "[[[1.+1.j]\n  [2.+2.j]]\n\n [[3.+3.j]\n  [4.+4.j]]]"
        assert (stream_results[0] == [1.0 + 1.0j, 2.0 + 2.0j]).all
