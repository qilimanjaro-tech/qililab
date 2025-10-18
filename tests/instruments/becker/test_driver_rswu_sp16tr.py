"""Tests for the DriverRSWUSP16TR class."""
import pytest
from typing import Any

from qililab.instruments.becker.driver_rswu_sp16tr import DriverRSWUSP16TR


class _FakeVisa:
    def __init__(self, idn="Becker Nachrichtentechnik, RSWU-SP16TR, P/N: 2506.4002.1, S/N: 2509002, HR: 1.00, SR: 1.0.1"):
        self._idn = idn
        self._active = "RF1"
        self.read_termination = "\n"
        self.write_termination = "\n"
        self.timeout = 5000

    def write(self, cmd: str) -> None:
        cmd = cmd.strip()
        if cmd.upper().startswith("ROUT:CHAN "):
            ch = cmd.split(" ", 1)[1].strip()
            self._active = ch

    def query(self, cmd: str) -> str:
        cmd = cmd.strip().upper()
        if cmd == "*IDN?":
            return self._idn
        if cmd == "ROUT:CHAN?":
            return self._active

        return ""

    def close(self) -> None:
        pass


@pytest.fixture()
def switch(monkeypatch) -> DriverRSWUSP16TR:
    """Instantiate the driver and replace its VISA handle with our stub."""
    drv = DriverRSWUSP16TR("sw", "TCPIP::192.168.0.10::5025::SOCKET")
    fake = _FakeVisa()
    # swap the underlying VISA resource
    monkeypatch.setattr(drv, "visa_handle", fake, raising=False)

    return drv


def test_idn_query(switch: DriverRSWUSP16TR):
    """Test idn_query."""
    rep = switch.idn()

    assert "RSWU-SP16TR" in rep


@pytest.mark.parametrize("ch", ["RF1", "RF6", "RF16"])
def test_active_channel_set_get(switch: DriverRSWUSP16TR, ch: str):
    """Test active channel."""
    switch.active_channel(ch)
    got = switch.active_channel()

    assert got == ch


def test_parser_accepts_lowercase(switch: DriverRSWUSP16TR, monkeypatch):
    """Test accepts_lowercase."""
    switch.visa_handle._active = "rf4"
    got = switch.active_channel()

    assert got == "RF4"


def test_parser_accepts_digits_directly():
    """Test parser accepts digits directly."""
    assert DriverRSWUSP16TR._parse_active_channel("6") == "RF6"
    assert DriverRSWUSP16TR._parse_active_channel("16") == "RF16"
    assert DriverRSWUSP16TR._parse_active_channel("XYZ") == "XYZ"


def test_route_convenience_method(switch: DriverRSWUSP16TR):
    """Test route_convenience_method."""
    switch.route("RF3")

    assert switch.active_channel() == "RF3"


def test_invalid_channel_raises_validation(switch: DriverRSWUSP16TR):
    """Test invalid_channek_raises_validation."""
    with pytest.raises(Exception):
        switch.active_channel("RF17")
