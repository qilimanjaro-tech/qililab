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
        settings_manager = SettingsManager()
        assert id(settings_manager) == id(SM)

    def test_load(self) -> None:
        """Test the load method of the SettingsManager class. Assert that the returned objects are of the correct type.
        Assert that errors are raised correctly."""
        assert isinstance(SM.load(name="qili", id="platform"), PlatformSettings)
        assert isinstance(SM.load(name="qubit", id="calibration"), QubitCalibrationSettings)
        with pytest.raises(FileNotFoundError):
            SM.load(name="unknown_name", id="unknown_id")
            SM.load(name="calibration", id="unknown_calibration")

    def test_dump(self) -> None:
        """Test the dump method of the SettingsManager class."""
        settings = SM.load(name="qili", id="platform")
        SM.dump(settings)
