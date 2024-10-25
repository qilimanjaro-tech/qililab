import pytest
from unittest.mock import MagicMock
from qililab.platform.components.buses import Buses
from qililab.platform.components.bus import Bus

@pytest.fixture
def mock_buses():
    bus1 = MagicMock(spec=Bus)
    bus2 = MagicMock(spec=Bus)
    bus1.alias = "bus1"
    bus2.alias = "bus2"
    bus1.has_adc.return_value = False
    bus2.has_adc.return_value = True
    return [bus1, bus2]

@pytest.fixture
def buses(mock_buses):
    return Buses(elements=mock_buses)

def test_buses_initialization(buses, mock_buses):
    assert len(buses) == len(mock_buses)
    assert buses.elements == mock_buses

def test_buses_add(buses):
    new_bus = MagicMock(spec=Bus)
    new_bus.alias = "bus3"
    buses.add(new_bus)
    assert len(buses) == 3
    assert buses.get("bus3") == new_bus

def test_buses_get_existing(buses, mock_buses):
    bus = buses.get("bus1")
    assert bus == mock_buses[0]

def test_buses_get_non_existing(buses):
    bus = buses.get("non_existent_bus")
    assert bus is None

def test_buses_len(buses):
    assert len(buses) == 2

def test_buses_iter(buses, mock_buses):
    buses_iter = iter(buses)
    assert list(buses_iter) == mock_buses

def test_buses_getitem(buses, mock_buses):
    assert buses[0] == mock_buses[0]
    assert buses[1] == mock_buses[1]

def test_buses_to_dict(buses, mock_buses):
    mock_buses[0].to_dict.return_value = {"alias": "bus1"}
    mock_buses[1].to_dict.return_value = {"alias": "bus2"}
    expected_dict = [{"alias": "bus1"}, {"alias": "bus2"}]
    assert buses.to_dict() == expected_dict

def test_buses_str(buses):
    mock_buses = buses.elements
    expected_str = f"{str(mock_buses[0])}\n{str(mock_buses[1])}"
    assert str(buses) == expected_str

def test_buses_readout_buses(buses, mock_buses):
    readout_buses = buses.readout_buses
    assert len(readout_buses) == 1
    assert readout_buses[0] == mock_buses[1]
