import pytest
from unittest.mock import MagicMock, patch
from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyInstrument
import qcodes.validators as vals
from qililab.buses.instruments.drive_bus import DriveBus
from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
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

class MockQcmQrmRF(DummyInstrument):

    def __init__(self, name, qcm_qrm, parent=None, slot_idx=0):
        super().__init__(name=name, gates=["dac1"])

        # local oscillator parameters
        channels = ["out0", "out1"]
        for channel in channels:
            self.add_parameter(
                name=f"{channel}_lo_freq",
                label="Frequency",
                unit="Hz",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )
            self.add_parameter(
                f"{channel}_lo_en",
                label="Status",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )

        # attenuator parameters
        for channel in channels:
            self.add_parameter(
                name=f"{channel}_att",
                label="Attenuation",
                unit="dB",
                get_cmd=None,
                set_cmd=None,
                get_parser=float,
                vals=vals.Numbers(0, 20e9),
            )

@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""

    return get_pulse_bus_schedule(start_time=0)

@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    sequencer = SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)

    return sequencer

@pytest.fixture(name="local_oscillator")
def fixture_local_oscillator() -> QcmQrmRfLo:
    """Return QcmQrmRfLo instance"""
    channel = "out0"
    lo_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm="qcm")
    local_oscillator = QcmQrmRfLo(name=f"test_lo_{channel}", parent=lo_parent, channel=channel)

    return local_oscillator

@pytest.fixture(name="attenuator")
def fixture_attenuator() -> QcmQrmRfAtt:
    """Return QcmQrmRfAtt instance"""
    channel = "out1"
    att_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm="qcm")
    attenuator = QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)

    return attenuator

class TestDriveBus:
    """Unit tests checking the DriveBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""

        Instrument.close_all()

    def test_init(self, sequencer: SequencerQCM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt):
        """Test init method"""
        qubit = 0
        drive_bus = DriveBus(qubit=qubit, awg=sequencer, local_oscillator=local_oscillator, attenuator=attenuator)

        assert (drive_bus.qubit == qubit)
        assert isinstance(drive_bus.awg, SequencerQCM)
        assert isinstance(drive_bus.local_oscillator, QcmQrmRfLo)
        assert isinstance(drive_bus.attenuator, QcmQrmRfAtt)

    def test_set(self, sequencer: SequencerQCM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt):
        """Test set method"""
        qubit = 0
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation
        drive_bus = DriveBus(qubit=qubit, awg=sequencer, local_oscillator=local_oscillator, attenuator=attenuator)
        drive_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        drive_bus.set(instrument_name="local_oscillator", param_name=lo_frequency_param, value=2)
        drive_bus.set(instrument_name="attenuator", param_name=attenuation_param, value=2)

        assert sequencer.get(sequencer_param) is True
        assert (local_oscillator.get(lo_frequency_param) == 2)
        assert (attenuator.get(attenuation_param) == 2)

    def test_get(self, sequencer: SequencerQCM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt):
        """Test get method"""
        qubit = 0
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation
        drive_bus = DriveBus(qubit=qubit, awg=sequencer, local_oscillator=local_oscillator, attenuator=attenuator)
        drive_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        drive_bus.set(instrument_name="local_oscillator", param_name=lo_frequency_param, value=2)
        drive_bus.set(instrument_name="attenuator", param_name=attenuation_param, value=2)

        assert drive_bus.get("awg", sequencer_param) is True
        assert (drive_bus.get("local_oscillator", lo_frequency_param) == 2)
        assert (drive_bus.get("attenuator", attenuation_param) == 2)

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute(self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, sequencer: SequencerQCM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt):
        """Test execute method"""
        qubit = 0
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        drive_bus = DriveBus(qubit=qubit, awg=sequencer, local_oscillator=local_oscillator, attenuator=attenuator)
        drive_bus.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, num_bins=num_bins)

        mock_execute.assert_called_once_with(pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, num_bins=num_bins)
