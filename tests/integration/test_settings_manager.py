import pytest

from qililab.platform import Platform
from qililab.platform.components import Qubit
from qililab.settings import SETTINGS_MANAGER
from qililab.settings.settings_manager import SettingsManager

SETTINGS_MANAGER.platform_name = "platform_0"


class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self):
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager(foldername="qili")
        assert id(settings_manager) == id(SETTINGS_MANAGER)

    def test_load_default_platform_settings(self):
        """Test the load method of the SettingsManager class with the default platform settings.
        Assert that errors are raised correctly."""
        settings = SETTINGS_MANAGER.load(filename="platform")
        Platform.PlatformSettings(**settings)

    def test_load_default_qubit_settings(self):
        """Test the load method of the SettingsManager class with the default qubit settings.
        Assert that errors are raised correctly."""
        settings = SETTINGS_MANAGER.load(filename="qubit_0")
        Qubit.QubitCalibrationSettings(**settings)

    def test_load_unknown_file(self):
        """Test the load method of the SettingsManager class with an unknown file."""
        with pytest.raises(FileNotFoundError):
            SETTINGS_MANAGER.load(filename="unknown_file")
