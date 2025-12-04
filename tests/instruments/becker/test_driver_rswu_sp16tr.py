"""Tests for the DriverRSWUSP16TR class."""
import pytest
from typing import Any
import pyvisa

from qililab.instruments.becker.driver_rswu_sp16tr import DriverRSWUSP16TR

@pytest.fixture(scope="function", name="rf_switchks")
def _make_rf_switchks():
    """
    Create a simulated Keysight E5080B instrument.
    The pyvisa_sim_file parameter instructs QCoDeS to use the simulation file.
    """
    driver = DriverRSWUSP16TR("RSWUSP16TR",
                              "TCPIP::192.168.0.10::5025::SOCKET",
                              pyvisa_sim_file="qililab.instruments.sims:RSWUSP16TR.yaml")
    yield driver
    driver.close()

def test_idn_query(rf_switchks: DriverRSWUSP16TR):
    """Test idn_query."""
    rep = rf_switchks.idn()

    assert "RSWU-SP16TR" in rep


@pytest.mark.parametrize("ch", ["RF1", "RF6", "RF16"])
def test_active_channel_set_get(rf_switchks: DriverRSWUSP16TR, ch: str):
    """Test active channel."""
    rf_switchks.active_channel(ch)
    got = rf_switchks.active_channel()

    assert got == ch


def test_parser_accepts_lowercase(rf_switchks: DriverRSWUSP16TR, monkeypatch):
    """Test accepts_lowercase."""
    rf_switchks.active_channel("rf4")
    got = rf_switchks.active_channel()

    assert got == "RF4"


def test_parser_accepts_digits_directly():
    """Test parser accepts digits directly."""
    assert DriverRSWUSP16TR._parse_active_channel("6") == "RF6"
    assert DriverRSWUSP16TR._parse_active_channel("16") == "RF16"
    assert DriverRSWUSP16TR._parse_active_channel("XYZ") == "XYZ"


def test_route_convenience_method(rf_switchks: DriverRSWUSP16TR):
    """Test route_convenience_method."""
    rf_switchks.route("RF3")

    assert rf_switchks.active_channel() == "RF3"


def test_invalid_channel_raises_validation(rf_switchks: DriverRSWUSP16TR):
    """Test invalid_channek_raises_validation."""
    with pytest.raises(Exception):
        rf_switchks.active_channel("RF17")
