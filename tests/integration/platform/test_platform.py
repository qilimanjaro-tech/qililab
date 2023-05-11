"""Tests for the Platform class."""
import pytest

from qililab import save_platform
from qililab.platform import Platform, build_platform
from tests.data import Galadriel
from tests.utils import platform_db, platform_yaml


@pytest.mark.parametrize("platform", [platform_db(runcard=Galadriel.runcard), platform_yaml(runcard=Galadriel.runcard)])
class TestPlatform:
    """Integration tests checking the Platform attributes and methods."""

    def test_platform_manager_dump_method(self, platform: Platform):
        """Test PlatformManager dump method."""
        save_platform(platform=platform)
        with pytest.raises(NotImplementedError):
            save_platform(platform=platform, database=True)


class TestPlatformManagerYAML:
    """Tests checking the Platform attributes and methods."""

    def test_build_method(self):
        """Test build method loading from YAML."""
        platform = build_platform(name="sauron", database=False)
        assert isinstance(platform, Platform)
