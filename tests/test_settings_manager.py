from pathlib import Path

import pytest

from qililab.settings.settings import Settings
from qililab.settings.settings_manager import SettingsManager


@pytest.fixture
def settings_manager() -> SettingsManager:
    """Test of the SettingsManager class instantiation.
    This function is used as input to other settings_manager tests.

    Returns:
        SettingsManager: Instance of the SettingsManager class.
    """
    # TODO: Add instantiation with other id's (instrument, calibration...) when the settings are available
    return SettingsManager(name="qili", id="platform")


class TestSettingsManager:
    """Unit tests checking the SettingsManager attributes and methods"""

    def test_attributes(self, settings_manager: SettingsManager) -> None:
        """Test the constructor of the SettingsManager class. Assert that the attributes are
        generated correctly, comparing them to some values of the 'settings/platform/qili.yml' file.

        Args:
            settings_manager (SettingsManager): Class used to load and dump the yaml settings.
        """
        assert settings_manager.name == "qili"
        assert settings_manager.id == "platform"
        assert settings_manager.settings.name == "qili"
        assert settings_manager.nqubits == 1

    def test_path(self, settings_manager: SettingsManager) -> None:
        """Test path property of the SettingsManager class.

        Args:
            settings_manager (SettingsManager): Class used to load and dump the yaml settings.
        """
        assert (
            settings_manager._path
            == Path(__file__).parent.parent / "src" / "qililab" / "settings" / "platform" / "qili.yml"
        )

    def test_load(self, settings_manager: SettingsManager) -> None:
        """Test the load method of the SettingsManager class.

        Args:
            settings_manager (SettingsManager): Class used to load and dump the yaml settings.
        """
        settings = settings_manager.load()
        assert isinstance(settings, Settings)

    def test_dump(self, settings_manager: SettingsManager) -> None:
        """Test the dump method of the SettingsManager class.

        Args:
            settings_manager (SettingsManager): Class used to load and dump the yaml settings.
        """
        settings_manager.dump()
