"""Tests for the RSWU-SP16TR class."""
import pytest
from unittest.mock import MagicMock

from qililab.instruments.becker.rswu_sp16tr import RSWUSP16TR
from qililab.instruments import ParameterNotFound
from qililab import Parameter


@pytest.fixture()
def switch(monkeypatch) -> RSWUSP16TR:
    """Create wrapper instance with a mocked device and device-active state."""
    sw = RSWUSP16TR({"alias": "rf_switch"})
    param = MagicMock()
    param.get.return_value = "RF1"
    dev = MagicMock()
    dev.active_channel = param
    sw.device = dev
    monkeypatch.setattr(sw, "is_device_active", lambda: True)

    return sw


def test_route_valid_updates_settings_and_calls_device(switch: RSWUSP16TR):
    """Test route valid updates."""
    switch.route("RF5")
    assert switch.active_channel == "RF5"
    switch.device.active_channel.assert_called_once_with("RF5")


@pytest.mark.parametrize("bad", ["RF0", "RF17", "SOMETHING", "",])
def test_route_invalid_raises_valueerror(switch: RSWUSP16TR, bad: str):
    """Test route invalid updates."""
    with pytest.raises(ValueError):
        switch.route(bad)


def test_query_active_reads_device_and_updates_settings(switch: RSWUSP16TR):
    """Test query active reads device and updates settings."""
    switch.device.active_channel.get.return_value = "RF9"
    got = switch.query_active()
    assert got == "RF9"
    assert switch.active_channel == "RF9"
    switch.device.active_channel.get.assert_called_once()


def test_initial_setup_noop_if_none(switch: RSWUSP16TR):
    """Test initial setup noop if none."""
    switch.settings.active_channel = None
    switch.initial_setup()
    switch.device.active_channel.assert_not_called()


def test_initial_setup_applies_if_present(switch: RSWUSP16TR):
    """Test initial setup applies."""
    switch.settings.active_channel = "RF12"
    switch.initial_setup()
    switch.device.active_channel.assert_called_once_with("RF12")


def test_update_settings_pulls_from_device(switch: RSWUSP16TR):
    """Test update settings pulls from device."""
    switch.device.active_channel.get.return_value = "RF7"
    switch.update_settings()
    assert switch.active_channel == "RF7"
    switch.device.active_channel.get.assert_called_once()


def test_set_parameter_active_channel_calls_route(switch: RSWUSP16TR, monkeypatch):
    """Test set parameter active channel."""
    called = {}
    monkeypatch.setattr(switch, "route", lambda ch: called.setdefault("ch", ch))
    switch.set_parameter(Parameter.RF_ACTIVE_CHANNEL, "RF3")
    assert called["ch"] == "RF3"


def test_set_parameter_unknown_raises(switch: RSWUSP16TR):
    """Test set parameter unknown raises."""
    with pytest.raises(ParameterNotFound):
        switch.set_parameter(Parameter.AMPLITUDE, "x")


def test_get_parameter_active_channel_reads_device(switch: RSWUSP16TR):
    """Test get parameter active channel reads device."""
    switch.device.active_channel.get.return_value = "RF8"
    val = switch.get_parameter(Parameter.RF_ACTIVE_CHANNEL)
    assert val == "RF8"
    assert switch.active_channel == "RF8"  # settings synced
    switch.device.active_channel.get.assert_called_once()


def test_get_parameter_unknown_raises(switch: RSWUSP16TR):
    """Test get parameter raises."""
    with pytest.raises(ParameterNotFound):
        switch.get_parameter(Parameter.AMPLITUDE)


def test_to_dict_returns_dict(switch: RSWUSP16TR):
    """Test to_dict."""
    d = switch.to_dict()
    assert isinstance(d, dict)


def test_turn_on_off_reset_do_not_error(switch: RSWUSP16TR):
    """Test turn_on_off reset."""
    switch.turn_on()
    switch.turn_off()
    switch.reset()
