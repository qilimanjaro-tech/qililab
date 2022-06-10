"""Tests for the PlatformManagerDB class."""
from unittest.mock import MagicMock, patch

from qililab import build_platform
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.platform import Platform

from ...utils import yaml_safe_load_side_effect


@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
class TestPlatformManagerDB:
    """Unit tests checking the Platform attributes and methods."""

    def test_build_method(self, mock_load: MagicMock):
        """Test build method."""
        platform = build_platform(name=DEFAULT_PLATFORM_NAME, database=True)
        assert isinstance(platform, Platform)
        mock_load.assert_called()
