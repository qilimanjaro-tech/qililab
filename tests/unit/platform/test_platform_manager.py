"""Tests for the PlatformManagerDB and the PlatformManagerYAML classes."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_DB, PLATFORM_MANAGER_YAML
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.platform import Platform

from ...utils import yaml_safe_load_side_effect


@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
class TestPlatformManagerDB:
    """Unit tests checking the Platform attributes and methods."""

    def test_build_method(self, mock_load: MagicMock):
        """Test build method."""
        platform = PLATFORM_MANAGER_DB.build(platform_name=DEFAULT_PLATFORM_NAME)
        assert isinstance(platform, Platform)
        mock_load.assert_called()

    def test_build_wrong_kwargs(self, mock_load: MagicMock):
        """Test build method using wrong arguments."""
        with pytest.raises(ValueError):
            PLATFORM_MANAGER_DB.build(wrong_argument=DEFAULT_PLATFORM_NAME)
        mock_load.assert_not_called()

    def test_build_wrong_kwargs_value(self, mock_load: MagicMock):
        """Test build method using wrong arguments."""
        with pytest.raises(ValueError):
            PLATFORM_MANAGER_DB.build(platform_name=234)  # type: ignore
        mock_load.assert_not_called()


@patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect)
class TestPlatformManagerYAML:
    """Unit tests checking the Platform attributes and methods."""

    def test_build_method(self, mock_load: MagicMock):
        """Test build method."""
        filepath = Path(__file__).parent.parent.parent.parent / "examples" / "all_platform.yml"
        platform = PLATFORM_MANAGER_YAML.build(filepath=str(filepath))
        assert isinstance(platform, Platform)
        mock_load.assert_called_once()

    def test_build_wrong_kwargs(self, mock_load: MagicMock):
        """Test build method using wrong arguments."""
        with pytest.raises(ValueError):
            PLATFORM_MANAGER_YAML.build(wrong_argument="foobar")
        mock_load.assert_not_called()

    def test_build_wrong_kwargs_value(self, mock_load: MagicMock):
        """Test build method using wrong arguments."""
        with pytest.raises(ValueError):
            PLATFORM_MANAGER_YAML.build(filepath=234)  # type: ignore
        mock_load.assert_not_called()
