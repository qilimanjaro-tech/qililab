import pytest
from unittest.mock import MagicMock, patch
from qililab.instruments import Instrument, Instruments
from qililab.instruments.qblox import QbloxQCM, QbloxQRM
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.result import Result
from qililab.result.qprogram import MeasurementResult
from qililab.platform import Bus

@pytest.fixture
def mock_instruments():
    instrument1 = MagicMock(spec=Instrument)
    instrument2 = MagicMock(spec=Instrument)
    instrument1.is_awg.return_value = False
    instrument1.is_adc.return_value = True
    instrument2.is_awg.return_value = True
    instrument2.is_adc.return_value = False
    return [instrument1, instrument2]

@pytest.fixture
def mock_platform_instruments():
    platform_instruments = MagicMock(spec=Instruments)
    platform_instruments.get_instrument.side_effect = lambda alias: MagicMock(spec=Instrument)
    return platform_instruments

@pytest.fixture
def bus_settings(mock_instruments, mock_platform_instruments):
    return {
        "alias": "bus1",
        "instruments": ["instrument1", "instrument2"],
        "channels": [None, None]
    }

@pytest.fixture
def bus(bus_settings, mock_platform_instruments):
    return Bus(settings=bus_settings, platform_instruments=mock_platform_instruments)

def test_bus_alias(bus):
    assert bus.alias == "bus1"

def test_bus_instruments(bus, mock_instruments):
    assert len(bus.instruments) == 2

def test_bus_channels(bus):
    assert len(bus.channels) == 2
    assert bus.channels == [None, None]

def test_bus_str(bus):
    expected_str = "Bus bus1:  ----|<MagicMock>|----|<MagicMock>|----"
    assert str(bus) == expected_str

def test_bus_equality(bus):
    other_bus = MagicMock(spec=Bus)
    other_bus.__str__.return_value = str(bus)
    assert bus == other_bus

def test_bus_inequality(bus):
    other_bus = MagicMock(spec=Bus)
    other_bus.__str__.return_value = "different_bus"
    assert bus != other_bus

def test_bus_to_dict(bus):
    expected_dict = {
        "alias": "bus1",
        "instruments": ["<MagicMock>", "<MagicMock>"],
        "channels": [None, None]
    }
    assert bus.to_dict() == expected_dict

def test_bus_has_awg(bus):
    assert bus.has_awg() is True

def test_bus_has_adc(bus):
    assert bus.has_adc() is True

def test_bus_set_parameter(bus, mock_instruments):
    parameter = MagicMock()
    value = 5
    bus.set_parameter(parameter, value)
    mock_instruments[0].set_parameter.assert_called_once()

def test_bus_get_parameter(bus, mock_instruments):
    parameter = MagicMock()
    bus.get_parameter(parameter)
    mock_instruments[0].get_parameter.assert_called_once()

def test_bus_upload_qpysequence(bus, mock_instruments):
    qpysequence = MagicMock()
    bus.upload_qpysequence(qpysequence)
    mock_instruments[0].upload_qpysequence.assert_called_once()

def test_bus_upload(bus, mock_instruments):
    bus.upload()
    mock_instruments[0].upload.assert_called_once()

def test_bus_run(bus, mock_instruments):
    bus.run()
    mock_instruments[0].run.assert_called_once()

def test_bus_acquire_result(bus, mock_instruments):
    result = MagicMock(spec=Result)
    mock_instruments[0].acquire_result.return_value = result
    assert bus.acquire_result() == result

def test_bus_acquire_qprogram_results(bus, mock_instruments):
    acquisitions = {"acq1": MagicMock(spec=AcquisitionData)}
    results = [MagicMock(spec=MeasurementResult)]
    mock_instruments[0].acquire_qprogram_results.return_value = results
    assert bus.acquire_qprogram_results(acquisitions) == results
