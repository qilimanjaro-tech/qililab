"""Unittest for BusDriver class"""
from unittest.mock import MagicMock, patch

import pytest
from qblox_instruments.native.spi_rack_modules import DummyD5aApi, DummyS4gApi
from qcodes import Instrument
from qcodes import validators as vals

from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.drivers.instruments.qblox.spi_rack import D5aDacChannel, S4gDacChannel
from qililab.platform.components import BusDriver, DriveBus, FluxBus, ReadoutBus
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name
NUM_SLOTS = 20
START_TIME_DEFAULT = 0
START_TIME_NON_ZERO = 4
PORT = 0
ALIAS = "bus_0"


# Instrument parameters for testing:
PATH0_OUT = 0
PATH1_OUT = 1
INTERMED_FREQ = 100e5
GAIN = 0.9
LO_FREQUENCY = 1e9
ATTENUATION = 20
ATT_ALIAS = "attenuator_0"
LO_ALIAS = "lo_readout"
AWG_ALIAS = "q0_readout"


# FIXURES FOR PULSE_BUS_SCHEDULES
def get_pulse_bus_schedule(start_time: int, negative_amplitude: bool = False, number_pulses: int = 1):
    """Returns a gaussian pulse bus schedule"""
    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=(-1 * PULSE_AMPLITUDE) if negative_amplitude else PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=start_time)
    timeline = [pulse_event for _ in range(number_pulses)]

    return PulseBusSchedule(timeline=timeline, port="test")


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return a PulseBusSchedule instance."""
    return get_pulse_bus_schedule(start_time=0)


# FIXTURES FOR INSTRUMENTS AND BUSES
@pytest.fixture(name="current_source")
def fixture_current_source() -> S4gDacChannel:
    """Return a S4gDacChannel instance."""
    mocked_parent = MagicMock()
    mocked_parent.api = DummyS4gApi(spi_rack=MagicMock(), module=0)
    return S4gDacChannel(parent=mocked_parent, name="test", dac=0)


@pytest.fixture(name="voltage_source")
def fixture_voltage_source() -> D5aDacChannel:
    """Return a D5aDacChannel instance."""
    mocked_parent = MagicMock()
    mocked_parent.api = DummyD5aApi(spi_rack=MagicMock(), module=0)
    return D5aDacChannel(parent=mocked_parent, name="test", dac=0)


@pytest.fixture(name="digitiser")
def fixture_digitiser() -> SequencerQRM:
    """Return a SequencerQRM instance."""
    digitiser = SequencerQRM(parent=MagicMock(), name="test", seq_idx=0)
    digitiser.add_parameter(name="path0_out", vals=vals.Ints(), set_cmd=None, initial_value=PATH0_OUT)
    digitiser.add_parameter(name="path1_out", vals=vals.Ints(), set_cmd=None, initial_value=PATH1_OUT)
    digitiser.add_parameter(
        name="intermediate_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=INTERMED_FREQ
    )
    digitiser.add_parameter(name="gain", vals=vals.Numbers(), set_cmd=None, initial_value=GAIN)
    return digitiser


@pytest.fixture(name="sequencer_qcm")
def fixture_sequencer_qcm() -> SequencerQCM:
    """Return a SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name=AWG_ALIAS, seq_idx=0)
    sequencer.add_parameter(name="path0_out", vals=vals.Ints(), set_cmd=None, initial_value=PATH0_OUT)
    sequencer.add_parameter(name="path1_out", vals=vals.Ints(), set_cmd=None, initial_value=PATH1_OUT)
    sequencer.add_parameter(
        name="intermediate_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=INTERMED_FREQ
    )
    sequencer.add_parameter(name="gain", vals=vals.Numbers(), set_cmd=None, initial_value=GAIN)
    return sequencer


@pytest.fixture(name="qcmqrm_lo")
def fixture_qcmqrm_lo() -> QcmQrmRfLo:
    """Return a QcmQrmRfLo instance."""
    return QcmQrmRfLo(parent=MagicMock(), name=LO_ALIAS, channel="test")


@pytest.fixture(name="qcmqrm_att")
def fixture_qcmqrm_att() -> QcmQrmRfAtt:
    """Return a QcmQrmRfAtt instance."""
    attenuator = QcmQrmRfAtt(parent=MagicMock(), name=ATT_ALIAS, channel="test")
    attenuator.add_parameter(name="lo_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=LO_FREQUENCY)
    return attenuator


@pytest.fixture(name="buses")
def fixture_buses(
    sequencer_qcm: SequencerQCM,
    qcmqrm_lo: QcmQrmRfLo,
    qcmqrm_att: QcmQrmRfAtt,
    digitiser: SequencerQRM,
    current_source: S4gDacChannel,
    voltage_source: D5aDacChannel,
) -> list[BusDriver]:
    """Return a list of bus drivers instances."""
    return [
        BusDriver(alias=ALIAS, port=PORT, awg=sequencer_qcm, distortions=[]),
        DriveBus(
            alias=ALIAS,
            port=PORT,
            awg=sequencer_qcm,
            local_oscillator=qcmqrm_lo,
            attenuator=qcmqrm_att,
            distortions=[],
        ),
        FluxBus(alias=ALIAS, port=PORT, awg=sequencer_qcm, source=current_source, distortions=[]),
        FluxBus(alias=ALIAS, port=PORT, awg=sequencer_qcm, source=voltage_source, distortions=[]),
        ReadoutBus(
            alias=ALIAS,
            port=PORT,
            awg=digitiser,
            local_oscillator=qcmqrm_lo,
            attenuator=qcmqrm_att,
            digitiser=digitiser,
            distortions=[],
        ),
    ]


class TestBusDriver:
    """Unit tests checking the DriveBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""
        Instrument.close_all()

    def test_init(self, buses: list[BusDriver]):
        """Test init method"""
        for bus in buses:
            assert bus.alias == ALIAS
            assert bus.port == PORT
            assert isinstance(bus.instruments["awg"], SequencerQCM)

    def test_set(self, buses: list[BusDriver]):
        """Test set method"""
        for bus in buses:
            # Testing with parameters that exists
            sequencer_param = "path0_out"
            bus.set(param_name=sequencer_param, value=2)
            assert bus.instruments["awg"].get(sequencer_param) == 2

            # Testing with parameter that does not exist
            random_param = "some_random_param"
            with pytest.raises(
                AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
            ):
                bus.set(param_name=random_param, value=True)

    def test_get(self, buses: list[BusDriver]):
        """Test get method"""
        for bus in buses:
            # Testing with parameters that exists
            sequencer_param = "path0_out"
            bus.set(param_name=sequencer_param, value=2)

            assert bus.get(sequencer_param) == 2

            # Testing with parameter that does not exist
            random_param = "some_random_param"
            with pytest.raises(
                AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
            ):
                bus.get(param_name=random_param)

    def test_set_get_delay(self, buses: list[BusDriver]):
        """Test set and get method for delay parameter"""
        for bus in buses:
            bus.set(param_name="delay", value=0.3)
            assert bus.get("delay") == 0.3

    def test_set_get_distortions(self, buses: list[BusDriver]):
        """Test set and get method for distortions parameter"""
        for bus in buses:
            with pytest.raises(
                NotImplementedError, match="Setting distortion parameters of a bus is not yet implemented."
            ):
                bus.set(param_name="distortions", value=[])
            with pytest.raises(
                NotImplementedError, match="Getting distortion parameters of a bus is not yet implemented."
            ):
                bus.get(param_name="distortions")

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, buses: list[BusDriver]):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1

        for bus in buses:
            bus.execute(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                num_bins=num_bins,
            )

            mock_execute.assert_called_with(
                pulse_bus_schedule=pulse_bus_schedule,
                nshots=nshots,
                repetition_duration=repetition_duration,
                num_bins=num_bins,
            )

    def test_eq(self, buses: list[BusDriver]):
        """Unittest for __eq__ method."""
        for bus in buses:
            assert "random str" != bus

    def test_to_dict(self, buses: list[BusDriver]):  # pylint: disable=too-many-branches
        # sourcery skip: merge-duplicate-blocks, remove-redundant-if, switch
        """Test that the to_dict method of the BusDriver base class works correctly."""
        for bus in buses:
            dictionary = bus.to_dict()

            # Check the basic bus dictionary part
            assert isinstance(dictionary, dict)
            assert dictionary["alias"] == ALIAS
            assert dictionary["port"] == PORT
            assert dictionary["type"] == bus.__class__.__name__
            assert dictionary["distortions"] == []

            # Check the instrument parameters dictionary part inside the bus dictionary
            for key, instrument_dict in dictionary.items():
                # Check the general structure of all the instrument dict
                if key not in ("alias", "port", "type", "distortions"):
                    assert key in BusDriver.instrument_interfaces_caps_translate()
                    assert isinstance(instrument_dict, dict)
                    assert isinstance(instrument_dict["alias"], str)
                    if "parameters" in instrument_dict:
                        assert isinstance(instrument_dict["parameters"], dict)

                # TEST ALIASES
                if key in ("VoltageSource", "CurrentSource", "Digitiser"):
                    assert instrument_dict["alias"] == "test"

                elif key == "LocalOscillator":
                    assert instrument_dict["alias"] == LO_ALIAS

                elif key == "Attenuator":
                    assert instrument_dict["alias"] == ATT_ALIAS

                elif key == "AWG":
                    if isinstance(bus, ReadoutBus):
                        assert instrument_dict["alias"] == "test"
                    else:
                        assert instrument_dict["alias"] == AWG_ALIAS

                # TEST PARAMETERS
                if key == "AWG":
                    assert (
                        instrument_dict["parameters"].items()
                        >= {
                            "path0_out": PATH0_OUT,
                            "path1_out": PATH1_OUT,
                            "intermediate_frequency": INTERMED_FREQ,
                            "gain": GAIN,
                        }.items()
                    )

                # Check that for the Readout Bus, the parameters has been printed only in the AWG, and not repeated in the Digitiser
                elif key == "Digitiser":
                    assert "parameters" not in instrument_dict

                elif key == "Attenuator":
                    assert instrument_dict["parameters"].items() >= {"lo_frequency": LO_FREQUENCY}.items()

    def test_serialization_without_setting_values(self, buses: list[BusDriver]):
        """Test that the to_dict & from_dict methods of the BusDriver base class work correctly together whenever we don't set values."""
        for bus in buses:
            if isinstance(bus, (DriveBus, FluxBus, ReadoutBus)):
                dictionary = bus.to_dict()

                with patch("qcodes.instrument.instrument_base.InstrumentBase.set") as mock_set:
                    new_bus = BusDriver.from_dict(dictionary, list(bus.instruments.values()))
                    mock_set.assert_called()
                    calls = mock_set.mock_calls

                new_dictionary = new_bus.to_dict()

                with patch("qcodes.instrument.instrument_base.InstrumentBase.set") as mock_set:
                    newest_bus = BusDriver.from_dict(new_dictionary, list(new_bus.instruments.values()))
                    mock_set.assert_called()
                    new_calls = mock_set.mock_calls

                newest_dictionary = newest_bus.to_dict()

                # Assert dictionaries and buses are the same, if we don't set anything
                assert dictionary == new_dictionary == newest_dictionary
                assert bus == new_bus == newest_bus

                # Test the calls are the same each time
                for index in range(
                    69
                ):  # Three are more depending on the bus, but from this number up, mockings start to appear that give problems with id's...
                    assert calls[index] == new_calls[index]
