"""Unit tests for all the methods for data management."""
import copy
from unittest.mock import MagicMock, patch

from qililab import build_platform
from qililab.platform import Platform
from tests.data import Galadriel


class TestBuildPlatform:
    """Unit tests for the `build_platform` function.."""

    @patch("qililab.data_management.yaml.safe_load", return_value=copy.deepcopy(Galadriel.runcard))
    @patch("qililab.data_management.open")
    def test_build_platform(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = build_platform(path="_")
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()

    @patch("qililab.data_management.yaml.safe_load", return_value=copy.deepcopy(Galadriel.runcard))
    @patch("qililab.data_management.open")
    def test_build_method_with_new_drivers(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = build_platform(path="_", new_drivers=True)
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()
