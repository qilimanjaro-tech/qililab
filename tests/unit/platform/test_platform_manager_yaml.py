"""Tests for PlatformManagerYAML class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab import build_platform
from qililab.platform import Platform

from ...side_effect import yaml_safe_load_side_effect


@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
class TestPlatformManagerYAML:
    """Unit tests checking the Platform attributes and methods."""

    def test_build_method(self, mock_load: MagicMock):
        """Test build method."""
        platform = build_platform(name="platform_0", database=False)
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        with pytest.raises(NotImplementedError):
            build_platform(name="platform_0", database=True)
