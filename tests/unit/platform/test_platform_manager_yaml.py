"""Tests for PlatformManagerYAML class."""
from unittest.mock import MagicMock, patch

import pytest

import qililab as ql
from qililab import build_platform, get_new_drivers_flag, set_new_drivers_flag
from qililab.platform import Platform

from ...data import Galadriel


class TestPlatformManagerYAML:
    """Unit tests checking the Platform attributes and methods."""
    @patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard)
    @patch("qililab.platform.platform_manager_yaml.open")
    def test_build_method(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test build method."""
        platform = build_platform(name="sauron", database=False)
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()
        mock_open.assert_called_once()
        with pytest.raises(NotImplementedError):
            build_platform(name="sauron", database=True)

    def test_new_drivers_flag_activation(self):
        """Test new drivers flag activation method."""
        value:bool = True
        set_new_drivers_flag(value=value)
        flag_value = get_new_drivers_flag()

        assert flag_value == value
