"""Unittest for testing readout_bus class methods"""
from unittest.mock import MagicMock, patch

import pytest
import qcodes.validators as vals
from qcodes import Instrument
from qcodes.tests.instrument_mocks import DummyInstrument

from qililab.drivers import parameters
from qililab.drivers.instruments.qblox.cluster import QcmQrmRfAtt, QcmQrmRfLo
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.platform.components import ReadoutBus
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


class MockQcmQrmRF(DummyInstrument):  # pylint: disable=abstract-method
    """Returns a mock instance of QcmQrmRF"""

    def __init__(self, name, qcm_qrm, parent=None, slot_idx=0):  # pylint: disable=unused-argument
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
    return SequencerQCM(parent=MagicMock(), name="test_sequencer", seq_idx=0)


@pytest.fixture(name="digitiser")
def fixture_digitiser() -> SequencerQRM:
    """Return SequencerQRM instance."""
    return SequencerQRM(parent=MagicMock(), name="test_digitiser", seq_idx=0)


@pytest.fixture(name="local_oscillator")
def fixture_local_oscillator() -> QcmQrmRfLo:
    """Return QcmQrmRfLo instance"""
    channel = "out0"
    lo_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm="qrm")

    return QcmQrmRfLo(name=f"test_lo_{channel}", parent=lo_parent, channel=channel)


@pytest.fixture(name="attenuator")
def fixture_attenuator() -> QcmQrmRfAtt:
    """Return QcmQrmRfAtt instance"""
    channel = "out1"
    att_parent = MockQcmQrmRF(f"test_qcmqrflo_{channel}", qcm_qrm="qcm")

    return QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)


@pytest.fixture(name="readout_bus")
def fixture_readout_bus(
    sequencer: SequencerQCM, digitiser: SequencerQRM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt
) -> ReadoutBus:
    """Return ReadoutBus instance"""
    return ReadoutBus(
        qubit=QUBIT, awg=sequencer, digitiser=digitiser, local_oscillator=local_oscillator, attenuator=attenuator
    )


class TestReadoutBus:
    """Unit tests checking the ReadoutBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""
        Instrument.close_all()

    def test_init(self, readout_bus: ReadoutBus):
        """Test init method"""

        assert readout_bus.qubit == QUBIT
        assert isinstance(readout_bus.awg, SequencerQCM)
        assert isinstance(readout_bus.digitiser, SequencerQRM)
        assert isinstance(readout_bus.local_oscillator, QcmQrmRfLo)
        assert isinstance(readout_bus.attenuator, QcmQrmRfAtt)

    def test_set(self, readout_bus: ReadoutBus):
        """Test set method"""
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation

        readout_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        readout_bus.set(instrument_name="digitiser", param_name=sequencer_param, value=True)
        readout_bus.set(instrument_name="local_oscillator", param_name=lo_frequency_param, value=2)
        readout_bus.set(instrument_name="attenuator", param_name=attenuation_param, value=2)

        assert readout_bus.awg.get(sequencer_param) is True
        assert readout_bus.digitiser.get(sequencer_param) is True
        assert readout_bus.local_oscillator.get(lo_frequency_param) == 2
        assert readout_bus.attenuator.get(attenuation_param) == 2

    def test_get(self, readout_bus: ReadoutBus):
        """Test get method"""
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation
        readout_bus.set(instrument_name="awg", param_name=sequencer_param, value=True)
        readout_bus.set(instrument_name="digitiser", param_name=sequencer_param, value=True)
        readout_bus.set(instrument_name="local_oscillator", param_name=lo_frequency_param, value=2)
        readout_bus.set(instrument_name="attenuator", param_name=attenuation_param, value=2)

        assert readout_bus.get("awg", sequencer_param) is True
        assert readout_bus.get("digitiser", sequencer_param) is True
        assert readout_bus.get("local_oscillator", lo_frequency_param) == 2
        assert readout_bus.get("attenuator", attenuation_param) == 2

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute_sequencer(
        self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, readout_bus: ReadoutBus
    ):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        readout_bus.execute(
            instrument_name="awg",
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

    @patch("qililab.drivers.instruments.qblox.sequencer_qrm.SequencerQRM.execute")
    def test_execute_digitiser(
        self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, readout_bus: ReadoutBus
    ):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        readout_bus.execute(
            instrument_name="digitiser",
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

    @patch("qililab.drivers.instruments.qblox.sequencer_qrm.SequencerQRM.get_results")
    def test_acquire_results(self, mock_acquire: MagicMock, readout_bus: ReadoutBus):
        """Test acquire_results method"""
        readout_bus.acquire_results()

        mock_acquire.assert_called_once()
