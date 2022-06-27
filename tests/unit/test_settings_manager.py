from unittest.mock import MagicMock, patch

import pytest

from qililab.constants import DEFAULT_PLATFORM_NAME, DEFAULT_SETTINGS_FOLDERNAME
from qililab.platform import Platform
from qililab.settings import SETTINGS_MANAGER, SettingsManager

from ..data import Galadriel


@patch("qililab.settings.settings_manager.yaml.safe_load")
class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self, mock_load: MagicMock):
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager()
        mock_load.assert_not_called()
        assert id(settings_manager) == id(SETTINGS_MANAGER)

    @patch("qililab.settings.settings_manager.open")
    def test_load_default_platform_settings(self, mock_open: MagicMock, mock_load: MagicMock):
        """Test the load method of the SettingsManager class with the default platform settings.
        Assert that errors are raised correctly."""
        mock_load.return_value = Galadriel.platform
        settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME,
            platform_name=DEFAULT_PLATFORM_NAME,
        )
        Platform.PlatformSettings(**settings)
        mock_load.assert_called()
        mock_open.assert_called()

    def test_load_unknown_file(self, mock_load: MagicMock):
        """Test the load method of the SettingsManager class with an unknown file."""
        with pytest.raises(FileNotFoundError):
            SETTINGS_MANAGER.load(foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name="unknown_platform")
        mock_load.assert_not_called()
