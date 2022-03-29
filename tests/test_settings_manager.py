import pytest

from qililab.settings import SM
from qililab.settings.abstract_settings import AbstractSettings
from qililab.settings.platform_settings import PlatformSettings
from qililab.settings.qubit_calibration_settings import QubitCalibrationSettings
from qililab.settings.settings_manager import SettingsManager


class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_singleton(self) -> None:
        """Test that SettingsManager is a singleton."""
        settings_manager = SettingsManager(foldername="qili")
        assert id(settings_manager) == id(SM)

    def test_load(self) -> None:
        """Test the load method of the SettingsManager class. Assert that the returned objects are of the correct type.
        Assert that errors are raised correctly."""
        assert isinstance(SM.load(filename="qili", settings_type="platform"), PlatformSettings)
        assert isinstance(
            SM.load(filename="qubit_0", settings_type="calibration", subfolder="qubit"), QubitCalibrationSettings
        )
        with pytest.raises(FileNotFoundError):
            SM.load(filename="unknown_name", settings_type="unknown_type")

    def test_dump(self) -> None:
        """Test the dump method of the SettingsManager class."""
        settings = SM.load(filename="qili", settings_type="platform")
        SM.dump(settings)
