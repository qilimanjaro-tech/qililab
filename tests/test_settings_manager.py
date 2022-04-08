import pytest

from qililab.settings import SETTINGS_MANAGER
from qililab.settings.platform import PlatformSettings
from qililab.settings.qubit import QubitCalibrationSettings
from qililab.settings.settings_manager import SettingsManager


class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self):
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager(foldername="qili")
        assert id(settings_manager) == id(SETTINGS_MANAGER)

    def test_load_default_platform_settings(self):
        """Test the load method of the SettingsManager class with the default platform settings.
        Assert that errors are raised correctly."""
        assert isinstance(SETTINGS_MANAGER.load(filename="platform"), PlatformSettings)

    def test_load_default_qubit_settings(self):
        """Test the load method of the SettingsManager class with the default qubit settings.
        Assert that errors are raised correctly."""
        assert isinstance(SETTINGS_MANAGER.load(filename="qubit_0"), QubitCalibrationSettings)

    def test_load_unknown_file(self):
        """Test the load method of the SettingsManager class with an unknown file."""
        with pytest.raises(FileNotFoundError):
            SETTINGS_MANAGER.load(filename="unknown_file")

    def test_dump_default_platform_settings(self):
        """Test the dump method of the SettingsManager class."""
        settings = SETTINGS_MANAGER.load(filename="platform")
        SETTINGS_MANAGER.dump(settings)
