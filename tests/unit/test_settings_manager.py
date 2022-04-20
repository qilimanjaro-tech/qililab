from unittest.mock import MagicMock, patch

import pytest

from qililab.settings import (
    SETTINGS_MANAGER,
    PlatformSettings,
    QubitCalibrationSettings,
)
from qililab.settings.settings_manager import SettingsManager

from .data import platform_settings_sample, qubit_0_settings_sample

SETTINGS_MANAGER.platform_name = "platform_0"


@patch("qililab.settings.settings_manager.yaml.safe_load")
class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self, mock_load: MagicMock):
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager(foldername="qili")
        mock_load.assert_not_called()
        assert id(settings_manager) == id(SETTINGS_MANAGER)

    def test_load_default_platform_settings(self, mock_load: MagicMock):
        """Test the load method of the SettingsManager class with the default platform settings.
        Assert that errors are raised correctly."""
        mock_load.return_value = platform_settings_sample
        settings = SETTINGS_MANAGER.load(filename="platform")
        PlatformSettings(**settings)

    def test_load_default_qubit_settings(self, mock_load: MagicMock):
        """Test the load method of the SettingsManager class with the default qubit settings.
        Assert that errors are raised correctly."""
        mock_load.return_value = qubit_0_settings_sample
        settings = SETTINGS_MANAGER.load(filename="qubit_0")
        QubitCalibrationSettings(**settings)

    def test_load_unknown_file(self, mock_load: MagicMock):
        """Test the load method of the SettingsManager class with an unknown file."""
        with pytest.raises(FileNotFoundError):
            SETTINGS_MANAGER.load(filename="unknown_file")
