"""Unit tests for all the methods for data management."""
import copy
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

import qililab as ql
from qililab.data_management import load_results, save_platform, save_results
from qililab.platform import Platform
from tests.data import Galadriel
from tests.test_utils import build_platform


@patch("qililab.data_management.yaml.safe_load", return_value=copy.deepcopy(Galadriel.runcard))
@patch("qililab.data_management.open")
class TestPlatformData:
    """Unit tests for the `build_platform` function.."""

    def test_build_platform(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = ql.build_platform(path="_")
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    def test_build_method_with_new_drivers(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = ql.build_platform(path="_", new_drivers=True)
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    def test_save_platform_with_non_yml_path(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test the `save_platform` function with a path that doesn't end in .yml."""
        path = save_platform(path="test/", platform=build_platform(Galadriel.runcard))

        mock_open.assert_called_once_with(file=Path(path), mode="w", encoding="utf-8")

        assert path == f"test/{Galadriel.name}.yml"
        mock_load.assert_not_called()

    def test_save_platform_with_yml_path(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test the `save_platform` function with a path that ends in .yml."""
        path = save_platform(path="test/test.yml", platform=build_platform(Galadriel.runcard))

        mock_open.assert_called_once_with(file=Path(path), mode="w", encoding="utf-8")

        assert path == "test/test.yml"
        mock_load.assert_not_called()


@patch("qililab.data_management.os.makedirs")
@patch("qililab.data_management.h5py.File")
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
