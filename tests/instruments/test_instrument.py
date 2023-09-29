"""Tests for the SystemControl class."""
import pytest

from qililab.platform import Platform
from qililab.system_control import SystemControl
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="system_control")
def fixture_system_control(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {"instruments": ["QCM", "rs_1"]}
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


class TestInstument:
    """Unit tests checking the ``SystemControl`` methods."""

    def test_error_raises_instrument_not_connected(self, system_control: SystemControl):
        """ "Test Parameter error raises if the parameter is not found."""
        with pytest.raises(AttributeError, match="Instrument Device has not been initialized"):
            system_control.set_parameter(parameter="voltage", value="45", channel_id=1)  # type: ignore
