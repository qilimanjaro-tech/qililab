"""Tests for the Platform class."""
import pytest

from qililab import save_platform
from qililab.platform import Platform

from ...conftest import platform_db, platform_yaml


@pytest.mark.parametrize("platform", [platform_db(), platform_yaml()])
class TestPlatform:
    """Integration tests checking the Platform attributes and methods."""

    def test_platform_manager_dump_method(self, platform: Platform):
        """Test PlatformManager dump method."""
        save_platform(platform=platform)
        with pytest.raises(NotImplementedError):
            save_platform(platform=platform, database=True)
