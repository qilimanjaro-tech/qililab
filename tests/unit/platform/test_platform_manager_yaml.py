"""Tests for PlatformManagerYAML class."""
from unittest.mock import MagicMock, patch

import pytest

from qililab import build_platform
from qililab.platform import Platform

from ...data import Galadriel


@patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard)
@patch("qililab.platform.platform_manager_yaml.open")
class TestPlatformManagerYAML:
    """Unit tests checking the Platform attributes and methods."""

    def test_build_method(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = build_platform(name="_", database=False)
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()
        with pytest.raises(NotImplementedError):
            build_platform(name="_", database=True)
