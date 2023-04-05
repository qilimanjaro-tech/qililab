"""Tests for the SGS100A class."""
import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instrument_controllers.yokogawa.gs200_controller import GS200Controller
from qililab.instruments.yokogawa.gs200 import GS200
from qililab.platform import Platform
from qililab.typings.enums import Parameter
from tests.data import SauronYokogawa


@pytest.fixture(name="yokogawa_gs200_controller")
def fixture_yokogawa_gs200_controller(platform: Platform):
    """Return an instance of GS200 controller class"""
    settings = copy.deepcopy(SauronYokogawa.yokogawa_gs200_controller)
    settings.pop("name")
    return GS200Controller(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="yokogawa_gs200_no_device")
def fixture_yokogawa_gs200_no_device():
    """Return an instance of GS200 class"""
    settings = copy.deepcopy(SauronYokogawa.yokogawa_gs200)
    settings.pop("name")
    return None
    return GS200(settings=settings)


@pytest.fixture(name="yokogawa_gs200")
@patch("qililab.instrument_controllers.yokogawa.gs200_controller.YokogawaGS200", autospec=True)
def fixture_yokogawa_gs200(mock_rs: MagicMock, yokogawa_gs200_controller: GS200Controller):
    """Return connected instance of SGS100A class"""
    # add dynamically created attributes
    mock_instance = mock_rs.return_value
    mock_instance.mock_add_spec(["output_status", "current_value"])
    yokogawa_gs200_controller.connect()
    return yokogawa_gs200_controller.modules[0]


class TestGS200:
    """Unit tests checking the SGS100A attributes and methods"""
