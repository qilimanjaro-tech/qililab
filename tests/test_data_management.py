"""Unit tests for all the methods for data management."""
import copy
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from ruamel.yaml import YAML

import qililab as ql
from qililab.data_management import load_results, save_platform, save_results
from qililab.platform import Platform
from tests.data import Galadriel
from tests.test_utils import build_platform


@patch("ruamel.yaml.YAML.load", return_value=copy.deepcopy(Galadriel.runcard))
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
            ql.build_platform()
        # We do it like this only for this case, best practice is to use match=... like in the following tests.
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

    def test_platform_serialization_from_imported_dict(self):
        """Test platform serialization by building a platform, saving it and then load it back again twice. Starting from a given dict."""
        original_dict = copy.deepcopy(Galadriel.runcard)
        # Check that the new serialization with ruamel.yaml.YAML().dump works for different formats...
        original_dict["gates_settings"]["gates"]["Y(0)"][0]["pulse"]["phase"] = 1.6707963267948966  # Test long decimals
        original_dict["instruments"][0]["awg_sequencers"][0]["intermediate_frequency"] = 100_000_000  # Test underscores
        original_dict["instruments"][1]["awg_sequencers"][0]["sampling_rate"] = 7.24730e09  # Test scientific notation
        original_dict["instruments"][4]["firmware"] = None  # Test None values

        original_platform = ql.build_platform(original_dict)

        path = save_platform(path="./test.yml", platform=original_platform)
        saved_platform = ql.build_platform(path)

        new_path = save_platform(path="./test.yml", platform=saved_platform)
        new_saved_platform = ql.build_platform(new_path)

        with open(file="./test.yml", mode="r", encoding="utf8") as generated_f:
            yaml = YAML(typ="safe")
            generated_f_dict = yaml.load(stream=generated_f)

        assert (
            original_platform.to_dict()
            == saved_platform.to_dict()
            == new_saved_platform.to_dict()
            == generated_f_dict
            == original_dict
        )
        os.remove(path)  # Cleaning generated file

    def test_platform_serialization_from_yaml_file(self):
        """Test platform serialization by building a platform, saving it and then load it back again twice. Starting from a yaml file."""
        original_platform = ql.build_platform("examples/runcards/galadriel.yml")
        path = save_platform(path="./test.yml", platform=original_platform)
        saved_platform = ql.build_platform(path)
        new_path = save_platform(path="./test.yml", platform=saved_platform)
        new_saved_platform = ql.build_platform(new_path)

        with open(file="examples/runcards/galadriel.yml", mode="r", encoding="utf8") as yaml_f:
            yaml = YAML(typ="safe")
            yaml_f_dict = yaml.load(stream=yaml_f)
        with open(file="./test.yml", mode="r", encoding="utf8") as generated_f:
            generated_f_dict = yaml.load(stream=generated_f)

        for i in ["name", "device_id", "chip", "instruments", "instrument_controllers"]:
            assert yaml_f_dict[i] == generated_f_dict[i]

        assert (
            original_platform.to_dict() == saved_platform.to_dict() == new_saved_platform.to_dict() == generated_f_dict
        )
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
