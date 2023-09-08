"""Unittest for testing readout_bus class methods"""
from unittest.mock import MagicMock, patch

import pytest
import qcodes.validators as vals
from qcodes import Instrument
from qcodes.instrument import DelegateParameter
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
PORT = 0
ALIAS = "readout_bus_0"


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
    attenuator = QcmQrmRfAtt(name=f"test_att_{channel}", parent=att_parent, channel=channel)
    attenuator.add_parameter(
        "status",
        label="Delegated parameter device status",
        source=att_parent.parameters[f"{channel}_lo_en"],
        parameter_class=DelegateParameter,
    )
    return attenuator


@pytest.fixture(name="readout_bus")
def fixture_readout_bus(digitiser: SequencerQRM, local_oscillator: QcmQrmRfLo, attenuator: QcmQrmRfAtt) -> ReadoutBus:
    """Return ReadoutBus instance"""
    return ReadoutBus(
        alias=ALIAS,
        port=PORT,
        awg=digitiser,
        digitiser=digitiser,
        local_oscillator=local_oscillator,
        attenuator=attenuator,
    )


class TestReadoutBus:
    """Unit tests checking the ReadoutBus attributes and methods. These tests mock the parent classes of the instruments,
    such that the code from `qcodes` is never executed."""

    def teardown_method(self):
        """Close all instruments after each test has been run"""
        Instrument.close_all()

    def test_init(self, readout_bus: ReadoutBus):
        """Test init method"""
        assert readout_bus.alias == ALIAS
        assert readout_bus.port == PORT
        assert isinstance(readout_bus.instruments["awg"], SequencerQCM)
        assert isinstance(readout_bus.instruments["digitiser"], SequencerQRM)
        assert isinstance(readout_bus.instruments["local_oscillator"], QcmQrmRfLo)
        assert isinstance(readout_bus.instruments["attenuator"], QcmQrmRfAtt)

    def test_set(self, readout_bus: ReadoutBus):
        """Test set method"""
        # Testing with parameters that exist
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation

        readout_bus.set(param_name=sequencer_param, value=True)
        readout_bus.set(param_name=lo_frequency_param, value=2)
        readout_bus.set(param_name=attenuation_param, value=2)

        assert readout_bus.instruments["awg"].get(sequencer_param) is True
        assert readout_bus.instruments["digitiser"].get(sequencer_param) is True
        assert readout_bus.instruments["local_oscillator"].get(lo_frequency_param) == 2
        assert readout_bus.instruments["attenuator"].get(attenuation_param) == 2

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            readout_bus.set(param_name=random_param, value=True)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            readout_bus.set(param_name=duplicated_param, value=True)

    def test_get(self, readout_bus: ReadoutBus):
        """Test get method"""
        # Testing with parameters that exist
        sequencer_param = "channel_map_path0_out0_en"
        lo_frequency_param = parameters.lo.frequency
        attenuation_param = parameters.attenuator.attenuation
        readout_bus.set(param_name=sequencer_param, value=True)
        readout_bus.set(param_name=sequencer_param, value=True)
        readout_bus.set(param_name=lo_frequency_param, value=2)
        readout_bus.set(param_name=attenuation_param, value=2)

        assert readout_bus.get(sequencer_param) is True
        assert readout_bus.get(sequencer_param) is True
        assert readout_bus.get(lo_frequency_param) == 2
        assert readout_bus.get(attenuation_param) == 2

        # Testing with parameter that does not exist
        random_param = "some_random_param"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} doesn't contain any instrument with the parameter {random_param}."
        ):
            readout_bus.get(param_name=random_param)

        # Testing with parameter that exists in more than one instrument
        duplicated_param = "status"
        with pytest.raises(
            AttributeError, match=f"Bus {ALIAS} contains multiple instruments with the parameter {duplicated_param}."
        ):
            readout_bus.get(param_name=duplicated_param)

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.execute")
    def test_execute_sequencer(
        self, mock_execute: MagicMock, pulse_bus_schedule: PulseBusSchedule, readout_bus: ReadoutBus
    ):
        """Test execute method"""
        nshots = 1
        repetition_duration = 1000
        num_bins = 1
        readout_bus.execute(
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

    def test_str(self, readout_bus: ReadoutBus):
        """Unittest for __str__ method."""
        expected_str = (
            f"{ALIAS} ({readout_bus.__class__.__name__}): "
            + "".join(f"--|{instrument.name}|" for instrument in readout_bus.instruments.values())
            + f"--> port {readout_bus.port}"
        )

        assert str(readout_bus) == expected_str