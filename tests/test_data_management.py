"""Unit tests for all the methods for data management."""
import copy
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import qililab as ql
from qililab.data_management import build_platform as dm_build_platform
from qililab.data_management import load_results, save_platform, save_results
from qililab.platform import Platform
from tests.data import Galadriel
from tests.test_utils import build_platform


@patch("qililab.data_management.yaml.safe_load", return_value=copy.deepcopy(Galadriel.runcard))
@patch("qililab.data_management.open")
class TestPlatformData:
    """Unit tests for the `build_platform` function.."""

    def test_build_platform_passing_a_path_to_old_path_argument(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        with pytest.warns() as record:
            platform = ql.build_platform(path="_")
        assert isinstance(platform, Platform)
        assert len(record) == 1
        assert (
            str(record[0].message)
            == "`path` argument is deprecated and will be removed soon. Use the `runcard` argument instead."
        )
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    def test_build_platform_passing_a_path_to_runcard_argument(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = ql.build_platform(runcard="_")
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    def test_build_platform_passing_a_dict_to_runcard_argument(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = ql.build_platform(runcard=copy.deepcopy(Galadriel.runcard))
        assert isinstance(platform, Platform)
        mock_load.assert_not_called()
        mock_open.assert_not_called()

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


class TestBuildPlatformCornerCases:
    """Unit tests for the corner cases of the `build_platform` function.."""

    def test_build_method_with_no_arguments(self):
        """Test build method with the new drivers."""
        with pytest.raises(ValueError) as no_arg_error:
            _ = ql.build_platform()

            (msg,) = no_arg_error.value.args
            assert msg == "`runcard` argument (str | dict) has not been passed to the `build_platform()` function."

    def test_build_method_with_old_path_and_new_runcard_arguments(self):
        """Test build method with the new drivers."""
        with pytest.raises(
            ValueError,
            match="Use only the `runcard` argument, `path` argument is deprecated.",
        ):
            _ = ql.build_platform(runcard="_", path="_")

    def test_build_method_with_new_drivers(self):
        """Test build method with the new drivers."""
        with pytest.raises(NotImplementedError, match="New drivers are not supported yet"):
            _ = ql.build_platform(runcard="_", new_drivers=True)

    def test_build_save_build_platform(self):
        """Test the workflow of the platform by building a platform, sving it and then load it back again"""
        original_platform = build_platform(Galadriel.runcard)
        path = save_platform(path="./test.yml", platform=original_platform)
        saved_platform = dm_build_platform(
            path
        )  # Needed this method instead of the mocked one in order to propperly read the generated test file

        assert saved_platform.to_dict() == original_platform.to_dict()
        os.remove(path)  # Cleaning generated file


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
