"""Test StreamArray"""

from unittest.mock import MagicMock, patch

import numpy as np

from qililab.result.result_management import load_results, save_results


@patch("qililab.result.result_management.os.makedirs")
@patch("qililab.result.result_management.h5py.File")
class TestResultsData:
    """Unit tests for the `save_results` function."""

    def test_save_results_path(self, mock_file: MagicMock, mock_makedirs: MagicMock):
        """Test that the path created to save the results is correct."""

        path = save_results(results=np.array([]), loops={"one_loop": np.arange(0, 100, 0.1)}, data_path="", name="test")

        mock_file.assert_called_once_with(f"{path}/results.h5", "w")
        assert mock_makedirs.call_count == 2
        mock_makedirs.assert_called_with(path)

        assert path.endswith("_test")

    def test_load_results(self, mock_file: MagicMock, mock_makedirs: MagicMock):
        """Test that the path created to save the results is correct."""

        path = "this_is_a_test/results.h5"

        # Create mock for the file context
        mock_hf = MagicMock()
        mock_file.return_value.__enter__.return_value = mock_hf

        # Mock results
        results_array = np.array([1, 2, 3])
        mock_results = MagicMock()
        mock_results.__getitem__.return_value = results_array
        mock_results.__array__ = lambda self: results_array

        # First loop: behaves like a dict (with attributes)
        loop = MagicMock()
        loop.__getitem__.return_value = np.array([10, 20])

        # Run the function
        load_results(path=path)

        # Mocks
        mock_file.assert_called_once_with(path, "r")
        mock_makedirs.assert_not_called()

    def test_load_results_with_dict_data(self, mock_file: MagicMock, mock_makedirs: MagicMock):
        """Test load_results handles loop data that is a dictionary with attributes."""

        path = "this_is_a_test/results.h5"

        # Create mock for the file context
        mock_hf = MagicMock()
        mock_file.return_value.__enter__.return_value = mock_hf

        # Mock results
        results_array = np.array([1, 2, 3])
        mock_results = MagicMock()
        mock_results.__getitem__.return_value = results_array
        mock_results.__array__ = lambda self: results_array

        # First loop: behaves like a dict (with attributes)
        loop = MagicMock()
        loop.__getitem__.return_value = {
            "array": np.array([10, 20]),
            "bus": "bus",
            "parameter": "parameter",
            "units": "units",
        }

        # Setup mock structure
        mock_loops_group = MagicMock()
        mock_loops_group.items.return_value = [("loop1", loop), ("loop2", loop)]

        mock_hf.__getitem__.side_effect = lambda key: {"loops": mock_loops_group, "results": mock_results}[key]

        # Run the function
        results, loops = load_results(path=path)

        np.testing.assert_array_equal(results, results_array)
        assert "loop1" in loops
        assert "loop2" in loops

        # Mocks
        mock_file.assert_called_once_with(path, "r")
        mock_makedirs.assert_not_called()
