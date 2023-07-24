from unittest.mock import MagicMock, patch

import pytest
import qcodes.validators as vals
from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.platform.components import FluxBus
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
    sequencer = SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)

    return sequencer


class TestFluxBus:
    """Unit tests checking the FluxBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init(self, sequencer: SequencerQCM):
        """Test init method"""
        flux_bus = FluxBus(source=sequencer)

        assert isinstance(flux_bus.source, SequencerQCM)

    def test_set(self, sequencer: SequencerQCM):
        """Test set method"""
        sequencer_param = "channel_map_path0_out0_en"
        flux_bus = FluxBus(source=sequencer)
        flux_bus.set(instrument_name="source", param_name=sequencer_param, value=True)

        assert sequencer.get(sequencer_param) is True

    def test_get(self, sequencer: SequencerQCM):
        """Test get method"""
        sequencer_param = "channel_map_path0_out0_en"
        flux_bus = FluxBus(source=sequencer)
        flux_bus.set(instrument_name="source", param_name=sequencer_param, value=True)

        assert flux_bus.get("source", sequencer_param) is True

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute_sequencer(
        self,
        mock_execute: MagicMock,
        pulse_bus_schedule: PulseBusSchedule,
        sequencer: SequencerQCM
    ):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        flux_bus = FluxBus(source=sequencer)
        flux_bus.execute(
            instrument_name="source",
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
