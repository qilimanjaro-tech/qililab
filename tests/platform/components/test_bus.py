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
    instrument1 = MagicMock(spec=QbloxQCM)
    instrument2 = MagicMock(spec=QbloxQRM)
    type(instrument1).alias = property(lambda self: "qcm")
    type(instrument2).alias = property(lambda self: "qrm")
    instrument1.is_awg.return_value = True
    instrument1.is_adc.return_value = False
    instrument2.is_awg.return_value = True
    instrument2.is_adc.return_value = True
    return [instrument1, instrument2]

@pytest.fixture
def bus(mock_instruments):
    settings = {
        "alias": "bus1",
        "instruments": ["qcm", "qrm"],
        "channels": [None, None]
    }
    return Bus(settings=settings, platform_instruments=Instruments(elements=mock_instruments))

def test_bus_alias(bus):
    assert bus.alias == "bus1"

def test_bus_instruments(bus):
    assert len(bus.instruments) == 2

def test_bus_channels(bus):
    assert len(bus.channels) == 2
    assert bus.channels == [None, None]

def test_bus_str(bus):
    assert isinstance(str(bus), str)

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
        "instruments": ["qcm", "qrm"],
        "channels": [None, None]
    }
    assert bus.to_dict() == expected_dict

def test_bus_has_awg(bus):
    assert bus.has_awg() is True

def test_bus_has_adc(bus):
    assert bus.has_adc() is True

def test_bus_set_parameter(bus):
    parameter = MagicMock()
    value = 5
    bus.set_parameter(parameter, value)
    bus.instruments[0].set_parameter.assert_called_once()

def test_bus_get_parameter(bus):
    parameter = MagicMock()
    bus.get_parameter(parameter)
    bus.instruments[0].get_parameter.assert_called_once()

def test_bus_upload_qpysequence(bus):
    qpysequence = MagicMock()
    bus.upload_qpysequence(qpysequence)
    bus.instruments[0].upload_qpysequence.assert_called_once()

def test_bus_upload(bus):
    bus.upload()
    bus.instruments[0].upload.assert_called_once()

def test_bus_run(bus):
    bus.run()
    bus.instruments[0].run.assert_called_once()

def test_bus_acquire_result(bus):
    result = MagicMock(spec=Result)
    bus.instruments[1].acquire_result.return_value = result
    assert bus.acquire_result() == result

def test_bus_acquire_qprogram_results(bus):
    acquisitions = {"acq1": MagicMock(spec=AcquisitionData)}
    results = [MagicMock(spec=MeasurementResult)]
    bus.instruments[1].acquire_qprogram_results.return_value = results
    assert bus.acquire_qprogram_results(acquisitions) == results
