"""Tests for the Attenuator class."""
import copy
import urllib
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.mini_circuits.mini_circuits_controller import MiniCircuitsController
from qililab.instruments import Attenuator
from qililab.platform import Platform
from qililab.typings.enums import Parameter
from tests.data import Galadriel
from tests.utils import platform_db


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return platform_db(runcard=Galadriel.runcard)


@pytest.fixture(name="attenuator_controller")
def fixture_attenuator_controller(platform: Platform) -> MiniCircuitsController:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    settings = copy.deepcopy(Galadriel.attenuator_controller_0)
    settings.pop("name")
    return MiniCircuitsController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="attenuator_no_device")
def fixture_attenuator_no_device() -> Attenuator:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    settings = copy.deepcopy(Galadriel.attenuator)
    settings.pop("name")
    return Attenuator(settings=settings)


@pytest.fixture(name="attenuator")
@patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
def fixture_attenuator(mock_urllib: MagicMock, attenuator_controller: MiniCircuitsController) -> Attenuator:
    """Load Schema.

    Returns:
        Schema: Instance of the Schema class.
    """
    attenuator_controller.connect()
    mock_urllib.request.Request.assert_called()
    mock_urllib.request.urlopen.assert_called()
    return attenuator_controller.modules[0]


class TestAttenuator:
    """Unit tests checking the Attenuator attributes and methods."""

    def test_id_property(self, attenuator_no_device: Attenuator):
        """Test id property."""
        assert attenuator_no_device.id_ == attenuator_no_device.settings.id_

    def test_category_property(self, attenuator_no_device: Attenuator):
        """Test category property."""
        assert attenuator_no_device.category == attenuator_no_device.settings.category

    def test_attenuation_property(self, attenuator: Attenuator):
        """Test attenuation property."""
        assert hasattr(attenuator, "attenuation")
        assert attenuator.attenuation == attenuator.settings.attenuation

    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    @pytest.mark.parametrize("parameter, value", [(Parameter.ATTENUATION, 0.01)])
    def test_setup_method(self, mock_urllib: MagicMock, attenuator: Attenuator, parameter: Parameter, value: float):
        """Test setup method."""
        attenuator.setup(parameter=parameter, value=value)
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()
        assert attenuator.settings.attenuation == value

    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_initial_setup_method(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test initial setup method."""
        attenuator.initial_setup()
        mock_urllib.request.Request.assert_called()
        mock_urllib.request.urlopen.assert_called()

    def test_turn_on_method(self, attenuator: Attenuator):
        """Test turn_on method."""
        attenuator.turn_on()

    def test_turn_off_method(self, attenuator: Attenuator):
        """Test turn_off method."""
        attenuator.turn_off()

    def test_reset_method(self, attenuator: Attenuator):
        """Test reset method."""
        attenuator.reset()

    @patch("qililab.typings.instruments.mini_circuits.urllib", autospec=True)
    def test_http_request_raises_error(self, mock_urllib: MagicMock, attenuator: Attenuator):
        """Test delta property."""
        mock_urllib.error.URLError = urllib.error.URLError  # type: ignore
        mock_urllib.request.urlopen.side_effect = urllib.error.URLError(reason="")  # type: ignore
        with pytest.raises(ValueError):
            attenuator.initial_setup()
        mock_urllib.request.urlopen.assert_called()
