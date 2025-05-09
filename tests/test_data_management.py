"""Unit tests for all the methods for data management."""

import copy
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tests.data import Galadriel
from tests.test_utils import build_platform

import qililab as ql
from qililab.data_management import save_platform
from qililab.platform import Platform


@patch("ruamel.yaml.YAML.load", return_value=copy.deepcopy(Galadriel.runcard))
@patch("qililab.data_management.open")
class TestPlatformData:
    """Unit tests for the `build_platform` function.."""

    def test_build_platform_passing_a_path_to_runcard_argument(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method, with a string path."""
        platform = ql.build_platform(runcard="_")
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    def test_build_platform_passing_a_dict_to_runcard_argument(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method, with a direct dict."""
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

    def test_build_platform_passing_invalid_runcard_argument(self):
        """Test build method, with invalid argument."""
        for runcard in [None, 1, 1.0, True, False, [], ()]:
            with pytest.raises(ValueError) as wrong_runcard_error:
                ql.build_platform(runcard=runcard)
            (msg,) = wrong_runcard_error.value.args
            assert (
                msg
                == f"Incorrect type for `runcard` argument in `build_platform()`. Expected (str | dict), got: {type(runcard)}"
            )

    def test_build_method_with_new_drivers(self):
        """Test build method with the new drivers."""
        with pytest.raises(NotImplementedError, match="New drivers are not supported yet"):
            _ = ql.build_platform(runcard="_", new_drivers=True)

    def test_platform_serialization_from_imported_dict(self):
        """Test platform serialization by building a platform, saving it and then load it back again twice. Starting from a given dict."""
        original_dict = copy.deepcopy(Galadriel.runcard)
        # Check that the new serialization with ruamel.yaml.YAML().dump works for different formats...
        original_dict["digital"]["gates"]["Y(0)"][0]["pulse"]["phase"] = 1.6707963267948966  # Test long decimals
        original_dict["instruments"][0]["awg_sequencers"][0]["intermediate_frequency"] = 100_000_000  # Test underscores
        original_dict["instruments"][1]["awg_sequencers"][0]["sampling_rate"] = 7.24730e09  # Test scientific notation

        original_platform = ql.build_platform(original_dict)

        path = save_platform(path="./test.yml", platform=original_platform)
        saved_platform = ql.build_platform(path)

        new_path = save_platform(path="./test.yml", platform=saved_platform)
        new_saved_platform = ql.build_platform(new_path)

        original_platform_dict = original_platform.to_dict()
        saved_platform_dict = saved_platform.to_dict()
        new_saved_platform_dict = new_saved_platform.to_dict()

        assert original_platform_dict == saved_platform_dict == new_saved_platform_dict
        os.remove(path)  # Cleaning generated file
