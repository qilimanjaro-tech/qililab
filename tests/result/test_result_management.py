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
        _ = load_results(path=path)

        mock_file.assert_called_once_with(path, "r")
        mock_makedirs.assert_not_called()
