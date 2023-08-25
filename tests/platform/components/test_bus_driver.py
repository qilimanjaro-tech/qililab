"""Unittest for BusDriver class"""
from unittest.mock import MagicMock, patch

import pytest
from qcodes import Instrument
from qcodes import validators as vals

from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.drive_bus import DriveBus
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
    """Return PulseBusSchedule instance."""
    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="drive_bus")
def fixture_drive_bus(sequencer: SequencerQCM, qcmqrm_lo: QcmQrmRfLo, qcmqrm_attenuator: QcmQrmRfAtt) -> DriveBus:
    """Return DriveBus instance."""
    return DriveBus(
        alias=ALIAS, port=PORT, awg=sequencer, local_oscillator=qcmqrm_lo, attenuator=qcmqrm_attenuator, distortions=[]
    )


@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name="q0_readout", seq_idx=0)
    sequencer.add_parameter(name="path0_out", vals=vals.Ints(), set_cmd=None, initial_value=0)
    sequencer.add_parameter(name="path1_out", vals=vals.Ints(), set_cmd=None, initial_value=1)
    sequencer.add_parameter(name="intermediate_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=100e5)
    sequencer.add_parameter(name="gain", vals=vals.Numbers(), set_cmd=None, initial_value=0.9)
    return sequencer


@pytest.fixture(name="qcmqrm_lo")
def fixture_qcmqrm_lo() -> QcmQrmRfLo:
    """Return SequencerQCM instance."""
    lo = QcmQrmRfLo(parent=MagicMock(), name="lo_readout", channel="test")
    lo.add_parameter(name="attenuation", vals=vals.Ints(), set_cmd=None, initial_value=20)
    return lo


@pytest.fixture(name="qcmqrm_attenuator")
def fixture_qcmqrm_attenuator() -> QcmQrmRfAtt:
    """Return SequencerQCM instance."""
    attenuator = QcmQrmRfAtt(parent=MagicMock(), name="attenuator_0", channel="test")
    attenuator.add_parameter(name="lo_frequency", vals=vals.Numbers(), set_cmd=None, initial_value=1e9)
    return attenuator


@pytest.fixture(name="instruments")
def fixture_instruments(sequencer: SequencerQCM, qcmqrm_lo: QcmQrmRfLo, qcmqrm_attenuator: QcmQrmRfAtt) -> list:
    """Return instrument dict instance."""
    return [sequencer, qcmqrm_lo, qcmqrm_attenuator]


@pytest.fixture(name="bus_dictionary")
def fixture_bus_dictionary() -> dict:
    """Returns a dictionary of a FluxBus instance."""
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

    def test_init(self, drive_bus: BusDriver):
        """Test init method"""
        assert drive_bus.alias == ALIAS
        assert drive_bus.port == PORT
        assert isinstance(drive_bus.instruments["awg"], SequencerQCM)

    def test_set(self, drive_bus: BusDriver):
        """Test set method"""
        # Testing with parameters that exists
        sequencer_param = "channel_map_path0_out0_en"
        drive_bus.set(param_name=sequencer_param, value=True)
        assert drive_bus.instruments["awg"].get(sequencer_param) is True

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            drive_bus.set(param_name=random_param, value=True)

    def test_get(self, drive_bus: BusDriver):
        """Test get method"""
        # Testing with parameters that exists
        sequencer_param = "channel_map_path0_out0_en"
        drive_bus.set(param_name=sequencer_param, value=True)

        assert drive_bus.get(sequencer_param) is True

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            drive_bus.get(param_name=random_param)

    def test_set_get_delay(self, drive_bus: BusDriver):
        """Test set and get method for delay parameter"""
        drive_bus.set(param_name="delay", value=0.3)
        assert drive_bus.get("delay") == 0.3

    def test_set_get_distortions(self, drive_bus: BusDriver):
        """Test set and get method for distortions parameter"""
        with pytest.raises(NotImplementedError, match="Setting distortion parameters of a bus is not yet implemented."):
            drive_bus.set(param_name="distortions", value=[])
        with pytest.raises(NotImplementedError, match="Getting distortion parameters of a bus is not yet implemented."):
            drive_bus.get(param_name="distortions")

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, drive_bus: BusDriver):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        drive_bus.execute(
            pulse_bus_schedule=pulse_bus_schedule,
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )

        mock_execute.assert_called_once_with(
            pulse_bus_schedule=pulse_bus_schedule,
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )

    def test_eq(self, drive_bus: BusDriver):
        """Unittest for __eq__ method."""
        assert "random str" != drive_bus

    def test_from_dict(
        self,
        bus_dictionary: dict,
        instruments: list,
        sequencer: SequencerQCM,
        qcmqrm_lo: QcmQrmRfLo,
        qcmqrm_attenuator: QcmQrmRfAtt,
    ):
        """Test that the from_dict method of the BusDriver base class calls the child ones correctly."""
        drive_bus = BusDriver.from_dict(bus_dictionary, instruments)

        assert isinstance(drive_bus, DriveBus)
        assert drive_bus.alias == ALIAS
        assert drive_bus.instruments["awg"] == sequencer
        assert str(drive_bus.instruments["local_oscillator"]) == str(qcmqrm_lo)
        assert str(drive_bus.instruments["attenuator"]) == str(qcmqrm_attenuator)
        assert drive_bus.port == PORT
        assert drive_bus.distortions == []
