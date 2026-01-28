import pytest
from unittest.mock import MagicMock, patch
from qililab.instruments import Instrument, Instruments
from qililab.instruments.qblox import QbloxQCM, QbloxQRM
from qililab.qprogram.qblox_compiler import AcquisitionData
from qililab.typings import Parameter
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
        "channels": [0, 0]
    }
    return Bus(settings=settings, platform_instruments=Instruments(elements=mock_instruments))

class TestBus:

    def test_bus_iter(self, bus):
        for i, (instrument, channel) in enumerate(bus):
            assert instrument == bus.instruments[i]
            assert channel == bus.channels[i]

    def test_bus_alias(self, bus):
        assert bus.alias == "bus1"

    def test_bus_instruments(self, bus):
        assert len(bus.instruments) == 2

    def test_bus_channels(self, bus):
        assert len(bus.channels) == 2
        assert bus.channels == [0, 0]

    def test_bus_str(self, bus):
        assert isinstance(str(bus), str)

    def test_bus_properties(self, bus):
        assert bus.delay == 0
        assert bus.distortions == []

    def test_bus_equality(self, bus):
        other_bus = MagicMock(spec=Bus)
        other_bus.__str__.return_value = str(bus)
        assert bus == other_bus

    def test_bus_inequality(self, bus):
        other_bus = MagicMock(spec=Bus)
        other_bus.__str__.return_value = "different_bus"
        assert bus != other_bus

    def test_bus_to_dict(self, bus):
        expected_dict = {
            "alias": "bus1",
            "instruments": ["qcm", "qrm"],
            "channels": [0, 0]
        }
        assert bus.to_dict() == expected_dict

    def test_bus_has_awg(self, bus):
        assert bus.has_awg() is True

    def test_bus_has_adc(self, bus):
        assert bus.has_adc() is True

    def test_bus_set_parameter(self, bus):
        parameter = MagicMock()
        value = 5
        bus.set_parameter(parameter, value)
        bus.instruments[0].set_parameter.assert_called_once()

    def test_get_outputid_from_channelid_raises_error(self, bus):
        bus.settings.instruments.append(bus.settings.instruments[1])
        bus.settings.channels = [1]
        with pytest.raises(Exception, match=f"No output_id was found to be associated with the bus with alias {bus.alias}"):
            bus._get_outputid_from_channelid()

    def test_bus_set_parameter_raises_error(self, bus):
        bus.settings.instruments = []
        bus.settings.channels = []
        with pytest.raises(Exception):
            bus.set_parameter(MagicMock(), 5)

    def test_bus_get_parameter(self, bus):
        parameter = MagicMock()
        bus.get_parameter(parameter)
        bus.instruments[0].get_parameter.assert_called_once()

    def test_bus_get_parameter_raises_error(self, bus):
        bus.settings.instruments = []
        bus.settings.channels = []
        with pytest.raises(Exception):
            bus.get_parameter(MagicMock())

    def test_bus_upload_qpysequence(self, bus):
        qpysequence = MagicMock()
        bus.upload_qpysequence(qpysequence)
        bus.instruments[0].upload_qpysequence.assert_called_once()

    def test_bus_upload_qpysequence_raises_error(self, bus):
        bus.settings.instruments = []
        bus.settings.channels = []
        with pytest.raises(AttributeError):
            bus.upload_qpysequence(MagicMock())

    def test_bus_upload(self, bus):
        bus.upload()
        bus.instruments[0].upload.assert_called_once()

    def test_bus_run(self, bus):
        bus.run()
        bus.instruments[0].run.assert_called_once()

    def test_bus_acquire_qprogram_results(self, bus):
        acquisitions = {"acq1": MagicMock(spec=AcquisitionData)}
        results = [MagicMock(spec=MeasurementResult)]
        bus.instruments[1].acquire_qprogram_results.return_value = results
        assert bus.acquire_qprogram_results(acquisitions) == results

    def test_bus_acquire_qprogram_results_raises_error(self, bus):
        acquisitions = {"acq1": MagicMock(spec=AcquisitionData)}
        bus.instruments.clear()
        bus.channels.clear()

        with pytest.raises(AttributeError, match=f"The bus {bus.alias} cannot acquire results because it doesn't have a readout system control."):
            _ = bus.acquire_qprogram_results(acquisitions)

    def test_bus_with_non_existant_instrument_raises_error(self, mock_instruments):
        with pytest.raises(NameError):
            settings = {
                "alias": "bus1",
                "instruments": ["not_in_instruments"],
                "channels": [None, None]
            }
            _ = Bus(settings=settings, platform_instruments=Instruments(elements=mock_instruments))

    def test_setup_trigger_network(self, bus, mock_instruments):
            # stub the private method on both mocks so they both have it
            mock_instruments[0]._setup_trigger_network = MagicMock()
            mock_instruments[1]._setup_trigger_network = MagicMock()

            # Call the helper under test
            bus._setup_trigger_network(trigger_address=7)

            # QbloxQRM is mock_instruments[1], channel 0
            mock_instruments[1]._setup_trigger_network.assert_called_once_with(
                trigger_address=7,
                sequencer_id=0
            )
            # The QCM should not receive the call
            mock_instruments[0]._setup_trigger_network.assert_not_called()
