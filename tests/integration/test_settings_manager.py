import pytest

from qililab.constants import (
    DEFAULT_PLATFORM_FILENAME,
    DEFAULT_PLATFORM_NAME,
    DEFAULT_SETTINGS_FOLDERNAME,
)
from qililab.platform import Platform, Qubit
from qililab.settings import SETTINGS_MANAGER, SettingsManager


class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self):
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager()
        assert id(settings_manager) == id(SETTINGS_MANAGER)

    def test_load_default_platform_settings(self):
        """Test the load method of the SettingsManager class with the default platform settings.
        Assert that errors are raised correctly."""
        settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME,
            platform_name=DEFAULT_PLATFORM_NAME,
            filename=DEFAULT_PLATFORM_FILENAME,
        )
        Platform.PlatformSettings(**settings)

    def test_load_default_qubit_settings(self):
        """Test the load method of the SettingsManager class with the default qubit settings.
        Assert that errors are raised correctly."""
        settings = SETTINGS_MANAGER.load(
            foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="qubit_0"
        )
        Qubit.QubitCalibrationSettings(**settings)

    def test_load_unknown_file(self):
        """Test the load method of the SettingsManager class with an unknown file."""
        with pytest.raises(FileNotFoundError):
            SETTINGS_MANAGER.load(
                foldername=DEFAULT_SETTINGS_FOLDERNAME, platform_name=DEFAULT_PLATFORM_NAME, filename="unknown_file"
            )
