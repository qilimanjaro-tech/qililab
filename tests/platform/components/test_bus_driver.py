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


@pytest.fixture(name="buses")
def fixture_buses(
    sequencer_qcm: SequencerQCM,
    qcmqrm_lo: QcmQrmRfLo,
    qcmqrm_attenuator: QcmQrmRfAtt,
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
            attenuator=qcmqrm_attenuator,
            distortions=[],
        ),
        FluxBus(alias=ALIAS, port=PORT, awg=sequencer_qcm, source=current_source, distortions=[]),
        FluxBus(alias=ALIAS, port=PORT, awg=sequencer_qcm, source=voltage_source, distortions=[]),
        ReadoutBus(
            alias=ALIAS,
            port=PORT,
            awg=sequencer_qcm,
            local_oscillator=qcmqrm_lo,
            attenuator=qcmqrm_attenuator,
            digitiser=digitiser,
            distortions=[],
        ),
    ]


@pytest.fixture(name="digitiser")
def fixture_sequencer() -> SequencerQRM:
    """Return a SequencerQRM instance."""
    return SequencerQRM(parent=MagicMock(), name="test", seq_idx=0)


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


@pytest.fixture(name="sequencer_qcm")
def fixture_sequencer_qcm() -> SequencerQCM:
    """Return a SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name="q0_readout", seq_idx=0)
    sequencer.add_parameter(name="path0_out", vals=vals.Ints(), set_cmd=None, initial_value=0)
    sequencer.add_parameter(name="path1_out", vals=vals.Ints(), set_cmd=None, initial_value=1)
    sequencer.add_parameter(name="intermediate_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=100e5)
    sequencer.add_parameter(name="gain", vals=vals.Numbers(), set_cmd=None, initial_value=0.9)
    return sequencer


@pytest.fixture(name="qcmqrm_lo")
def fixture_qcmqrm_lo() -> QcmQrmRfLo:
    """Return a QcmQrmRfLo instance."""
    lo = QcmQrmRfLo(parent=MagicMock(), name="lo_readout", channel="test")
    lo.add_parameter(name="attenuation", vals=vals.Ints(), set_cmd=None, initial_value=20)
    return lo


@pytest.fixture(name="qcmqrm_attenuator")
def fixture_qcmqrm_attenuator() -> QcmQrmRfAtt:
    """Return a QcmQrmRfAtt instance."""
    attenuator = QcmQrmRfAtt(parent=MagicMock(), name="attenuator_0", channel="test")
    attenuator.add_parameter(name="lo_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=1e9)
    return attenuator


@pytest.fixture(name="drive_bus_instruments")
def fixture_drive_bus_instruments(
    sequencer_qcm: SequencerQCM, qcmqrm_lo: QcmQrmRfLo, qcmqrm_attenuator: QcmQrmRfAtt
) -> list:
    """Return a list of instrument instances."""
    return [sequencer_qcm, qcmqrm_lo, qcmqrm_attenuator]


@pytest.fixture(name="drive_bus_dictionary")
def fixture_drive_bus_dictionary() -> dict:
    """Returns a dictionary of a DriveBus instance."""
    return {
        "alias": ALIAS,
        "type": "DriveBus",
        "AWG": {
            "alias": "q0_readout",
            "parameters": {
                "path0_out": 0,
                "path1_out": 1,
                "intermediate_frequency": 100e5,
                "gain": 0.9,
            },
        },
        "LocalOscillator": {
            "alias": "lo_readout",
            "parameters": {
                "lo_frequency": 1e9,
            },
        },
        "Attenuator": {
            "alias": "attenuator_0",
            "parameters": {
                "attenuation": 20,
            },
        },
        "port": PORT,
        "distortions": [],
    }


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
            bus.set(param_name=sequencer_param, value=1)
            assert bus.instruments["awg"].get(sequencer_param) == 1

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
            bus.set(param_name=sequencer_param, value=1)

            assert bus.get(sequencer_param) == 1

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

    def test_from_dict(
        self,
        drive_bus_dictionary: dict,
        drive_bus_instruments: list,
        sequencer_qcm: SequencerQCM,
        qcmqrm_lo: QcmQrmRfLo,
        qcmqrm_attenuator: QcmQrmRfAtt,
    ):
        """Test that the from_dict method of the BusDriver base class works correctly."""
        drive_bus = BusDriver.from_dict(drive_bus_dictionary, drive_bus_instruments)

        assert isinstance(drive_bus, DriveBus)
        assert drive_bus.alias == ALIAS
        assert drive_bus.instruments["awg"] == sequencer_qcm
        assert str(drive_bus.instruments["local_oscillator"]) == str(qcmqrm_lo)
        assert str(drive_bus.instruments["attenuator"]) == str(qcmqrm_attenuator)
        assert drive_bus.port == PORT
        assert drive_bus.distortions == []

    def test_to_dict(self, buses: list[BusDriver]):
        """Test that the to_dict method of the BusDriver base class works correctly."""
        for bus in buses:
            dictionary = bus.to_dict()

            assert isinstance(dictionary, dict)

            assert dictionary["alias"] == ALIAS
            assert dictionary["port"] == PORT
            assert dictionary["type"] == bus.__class__.__name__
            assert dictionary["distortions"] == []

            for key, instrument_dict in dictionary.items():
                if key not in ("alias", "port", "type", "distortions"):
                    assert key in BusDriver.caps_translate_dict()
                    assert (
                        isinstance(instrument_dict, dict)
                        and isinstance(instrument_dict["parameters"], dict)
                        and isinstance(instrument_dict["alias"], str)
                    )

    # TODO: Problems with 1) the Mocking in the instruments, 2) and about still passing the old instruments in the 2n iteration maybe?
    # def test_serialization_starting_from_dict(self, drive_bus_dictionary: dict, drive_bus_instruments: list):
    #     """Test that the todict & from_dict methods of the BusDriver base class work correctly together."""
    #     drive_bus = BusDriver.from_dict(drive_bus_dictionary, drive_bus_instruments)
    #     dictionary = drive_bus.to_dict()

    #     new_drive_bus = BusDriver.from_dict(dictionary, drive_bus_instruments)
    #     new_dictionary = new_drive_bus.to_dict()

    #     assert drive_bus_dictionary == dictionary == new_dictionary

    # # TODO: For this to work, I would need to pass the corresponding instruments for each bus.
    # def test_serialization_starting_from_class(self, buses: list[BusDriver], drive_bus_instruments: list):
    #     """Test that the to_dict method of the BusDriver base class works correctly."""
    #     for bus in buses:
    #         dictionary = bus.to_dict()
    #         new_bus = BusDriver.from_dict(dictionary, drive_bus_instruments)
    #         new_dictionary = bus.to_dict()

    #         assert dictionary == new_dictionary
    #         assert bus == new_bus
