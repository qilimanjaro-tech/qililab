import pytest

from qililab.settings import (
    SETTINGS_MANAGER,
    PlatformSettings,
    QubitCalibrationSettings,
)
from qililab.settings.settings_manager import SettingsManager


@pytest.fixture(name="settings_manager")
def fixture_sm() -> SettingsManager:
    """Fixture returning a settings manager for the platform platform_0"""
    SETTINGS_MANAGER.platform_name = "platform_0"
    return SETTINGS_MANAGER


class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self):
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager(foldername="qili")
        assert id(settings_manager) == id(SETTINGS_MANAGER)

    def test_load_default_platform_settings(self, settings_manager: SettingsManager):
        """Test the load method of the SettingsManager class with the default platform settings.
        Assert that errors are raised correctly."""
        settings = settings_manager.load(filename="platform")
        PlatformSettings(**settings)

    def test_load_default_qubit_settings(self, settings_manager: SettingsManager):
        """Test the load method of the SettingsManager class with the default qubit settings.
        Assert that errors are raised correctly."""
        settings = settings_manager.load(filename="qubit_0")
        QubitCalibrationSettings(**settings)

    def test_load_unknown_file(self, settings_manager: SettingsManager):
        """Test the load method of the SettingsManager class with an unknown file."""
        with pytest.raises(FileNotFoundError):
            settings_manager.load(filename="unknown_file")
