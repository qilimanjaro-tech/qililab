"""Unittest for BusDriver class"""
from unittest.mock import MagicMock, patch

import pytest
import qcodes.validators as vals
from qcodes import Instrument
from qcodes.instrument import DelegateParameter
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.platform.components.bus_driver import BusDriver
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
QUBIT = 0
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

    return PulseBusSchedule(timeline=timeline, port=0)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    return SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)


@pytest.fixture(name="bus")
def fixture_drive_bus(sequencer: SequencerQCM) -> BusDriver:
    """Return DriveBus instance"""
    return BusDriver(alias=ALIAS, qubit=QUBIT, awg=sequencer)


class TestBusDriver:
    """Unit tests checking the DriveBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""
        Instrument.close_all()

    def test_init(self, bus: BusDriver):
        """Test init method"""
        assert bus.alias == ALIAS
        assert bus.qubit == QUBIT
        assert isinstance(bus.instruments["awg"], SequencerQCM)

    def test_set(self, bus: BusDriver):
        """Test set method"""
        # Testing with parameters that exists
        sequencer_param = "channel_map_path0_out0_en"
        bus.set(param_name=sequencer_param, value=True)
        assert bus.instruments["awg"].get(sequencer_param) is True

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            bus.set(param_name=random_param, value=True)

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

    def test_set_get_delay(self, bus: BusDriver):
        """Test set and get method for delay parameter"""
        bus.set(param_name="delay", value=0.3)
        assert bus.get("delay") == 0.3

    def test_set_get_distortions(self, bus: BusDriver):
        """Test set and get method for distortions parameter"""
        with pytest.raises(NotImplementedError, match="This feature is not yet implemented."):
            bus.set(param_name="distortions", value=[])
        with pytest.raises(NotImplementedError, match="This feature is not yet implemented."):
            bus.get(param_name="distortions")

    def test_eq(self, bus: BusDriver):
        """Test comparing two Bus objects"""
        assert bus.__eq__(bus) is True

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, bus: BusDriver):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        bus.execute(
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
