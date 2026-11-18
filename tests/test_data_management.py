"""Unit tests for all the methods for data management."""

import copy
import os
from pathlib import Path
from unittest.mock import patch

import pytest

import qililab as ql
from qililab.data_management import build_platform, save_platform
from qililab.platform import Platform
from tests.data import Galadriel


class TestPlatformData:
    """Unit tests for the `build_platform` function.."""

    def test_build_platform_passing_a_path_to_runcard_argument(self):
        """Test build method, with a string path."""
        platform = ql.build_platform(runcard=Galadriel.runcard)
        assert isinstance(platform, Platform)

    def test_build_platform_passing_a_dict_to_runcard_argument(self):
        """Test build method, with a direct dict."""
        platform = ql.build_platform(runcard=copy.deepcopy(Galadriel.runcard))
        assert isinstance(platform, Platform)

    def test_save_platform_with_non_yml_path(self):
        """Test the `save_platform` function with a path that doesn't end in .yml."""
        platform = build_platform(Galadriel.runcard)
        path = save_platform(path="tests/", platform=platform)
        assert Path(path) == Path(f"tests/{Galadriel.name}.yml")
        Path(path).unlink(missing_ok=True)

    def test_save_platform_with_yml_path(self):
        """Test the `save_platform` function with a path that ends in .yml."""
        path = save_platform(path="tests/test.yml", platform=build_platform(Galadriel.runcard))
        assert Path(path) == Path("tests/test.yml")
        Path(path).unlink(missing_ok=True)

    def test_save_platform_preserves_existing_file_on_dump_error(self, tmp_path):
        """If serialisation fails, `save_platform` must leave an existing runcard untouched (QHC-1777).

        Before the fix the target was opened in write mode up-front, truncating it to 0 bytes
        before the (failing) dump, which destroyed the previous runcard.
        """
        target = tmp_path / "runcard.yml"
        original_content = "name: existing_runcard\n"
        target.write_text(original_content, encoding="utf-8")

        platform = build_platform(Galadriel.runcard)

        with patch("qililab.data_management.YAML") as mock_yaml:
            mock_yaml.return_value.dump.side_effect = RuntimeError("cannot represent an object")
            with pytest.raises(RuntimeError, match="cannot represent an object"):
                save_platform(path=str(target), platform=platform)

        # The existing file keeps its content instead of being truncated.
        assert target.read_text(encoding="utf-8") == original_content
        # The failed save leaves no leftover temporary files behind.
        assert [p.name for p in tmp_path.iterdir()] == ["runcard.yml"]


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
        # Test long decimals
        original_dict["digital"]["gates"]["Y(0)"][0]["phase"] = 1.6707963267948966
        # Test underscores
        original_dict["instruments"][0]["awg_sequencers"][0]["intermediate_frequency"] = 100_000_000
        # Test scientific notation
        original_dict["instruments"][1]["awg_sequencers"][0]["sampling_rate"] = 7.24730e09
        # Test bus delay
        original_dict["buses"][0]["delay"] = 12

        original_platform = ql.build_platform(original_dict)

        path = save_platform(path="./test.yml", platform=original_platform)
        saved_platform = ql.build_platform(path)

        new_path = save_platform(path="./test.yml", platform=saved_platform)
        new_saved_platform = ql.build_platform(new_path)

        original_platform_dict = original_platform.to_dict()
        saved_platform_dict = saved_platform.to_dict()
        new_saved_platform_dict = new_saved_platform.to_dict()

        assert original_platform_dict == saved_platform_dict == new_saved_platform_dict
        # A field missing from to_dict passes the comparison above, so check the reloaded delay itself
        assert saved_platform.buses.get(alias="drive_line_q0_bus").delay == 12
        # Cleaning generated file
        os.remove(path)
