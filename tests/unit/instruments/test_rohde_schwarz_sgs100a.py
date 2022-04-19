from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments import SGS100A
from qililab.settings import SETTINGS_MANAGER

SETTINGS_MANAGER.platform_name = "platform_0"


@pytest.fixture(name="rohde_schwarz")
@patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
def fixture_rohde_schwarz(mock_pulsar: MagicMock):
    """Return connected instance of SGS100A class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(["power", "frequency"])
    # connect to instrument
    rohde_schwarz_settings = SETTINGS_MANAGER.load(filename="rohde_schwarz_0")
    rohde_schwarz = SGS100A(name="rohde_schwarz", settings=rohde_schwarz_settings)
    rohde_schwarz.connect()
    return rohde_schwarz


class TestSGS100A:
    """Unit tests checking the SGS100A attributes and methods"""

    def test_connect_method_raises_error(self, rohde_schwarz: SGS100A):
        """Test that calling again connect raises a ValueError"""
        with pytest.raises(ValueError):
            rohde_schwarz.connect()

    def test_start_method(self, rohde_schwarz: SGS100A):
        """Test start method"""
        rohde_schwarz.start()
        rohde_schwarz.device.on.assert_called_once()  # type: ignore

    def test_setup_method(self, rohde_schwarz: SGS100A):
        """Test setup method"""
        rohde_schwarz.setup()
        rohde_schwarz.device.power.assert_called_once_with(rohde_schwarz.settings.power)
        rohde_schwarz.device.frequency.assert_called_once_with(rohde_schwarz.settings.frequency)

    def test_stop_method(self, rohde_schwarz: SGS100A):
        """Test stop method"""
        rohde_schwarz.stop()
        rohde_schwarz.device.off.assert_called_once()  # type: ignore

    def test_close_method(self, rohde_schwarz: SGS100A):
        """Test close method"""
        rohde_schwarz.close()
        rohde_schwarz.device.off.assert_called_once()  # type: ignore
        rohde_schwarz.device.close.assert_called_once()  # type: ignore
