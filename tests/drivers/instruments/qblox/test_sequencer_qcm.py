"""Tests for the SequencerQCM class."""
# pylint: disable=protected-access
from textwrap import dedent
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.sequence import Sequence as QpySequence
from qpysequence.weights import Weights

from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from tests.test_utils import is_q1asm_equal

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

    return PulseBusSchedule(timeline=timeline, port="0")


def get_envelope():
    """Returns a gaussian pulse bus schedule envelope"""

    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )

    return pulse.envelope()


expected_program_str_0 = """
setup:
                move             1, R0
                wait_sync        4

average:
                move             0, R1
bin:
                reset_ph
                set_awg_gain     32767, 32767
                set_ph           0
                play             0, 1, 4
long_wait_1:
                wait             996

                add              R1, 1, R1
                nop
                jlt              R1, 1, @bin
                loop             R0, @average
stop:
                stop
"""
expected_program_str_1 = """
setup:
                move             1, R0
                wait_sync        4

average:
                move             0, R1
bin:
long_wait_1:


                reset_ph
                set_awg_gain     32767, 32767
                set_ph           0
                play             0, 1, 4
long_wait_2:
                wait             996

                add              R1, 1, R1
                nop
                jlt              R1, 1, @bin
                loop             R0, @average
stop:
                stop
"""


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""

    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="pulse_bus_schedule_repeated_pulses")
def fixture_pulse_bus_schedule_repeated_pulses() -> PulseBusSchedule:
    """Return PulseBusSchedule instance with same pulse repeated."""

    return get_pulse_bus_schedule(start_time=0, number_pulses=3)


@pytest.fixture(name="pulse_bus_schedule_negative_amplitude")
def fixture_pulse_bus_schedule_negative_amplitude() -> PulseBusSchedule:
    """Return PulseBusSchedule instance with same pulse repeated."""

    return get_pulse_bus_schedule(start_time=0, negative_amplitude=True)


@pytest.fixture(name="sequencer")
def fixture_sequencer() -> SequencerQCM:
    """Return SequencerQCM instance."""
    return SequencerQCM(parent=MagicMock(), name="test", seq_idx=4)


class TestSequencer:
    """Unit tests checking the Sequencer attributes and methods"""

    def test_init(self):
        """Unit tests for init method"""

        sequencer_name = "test_sequencer_init"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        assert sequencer.get("swap_paths") is False

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._map_outputs")
    @pytest.mark.parametrize("path0", [0, 1])
    def test_set_with_qililab_path(self, mock_map_outputs: MagicMock, path0: int):
        """Unit tests for set method with qililab path"""
        sequencer_name = "test_sequencer_set_qililab_path"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequencer.set("path0", path0)
        mock_map_outputs.assert_called_once_with("path0", path0)

    def test_set_with_qblox_parameter(self, sequencer):
        """Unit tests for set method with qblox parameter"""
        sequencer.set("channel_map_path0_out0_en", True)
        assert sequencer.get("channel_map_path0_out0_en") is True

    @pytest.mark.parametrize("path0", [0, 1, 10])
    def test_map_outputs(self, sequencer, path0: int):
        """Unit tests for _map_outputs method"""
        if path0 == 10:
            error_str = f"Impossible path configuration detected. path0 cannot be mapped to output {path0}."
            with pytest.raises(ValueError, match=error_str):
                sequencer._map_outputs("path0", path0)
                assert sequencer.get("swap_paths") is False

        else:
            sequencer._map_outputs("path0", path0)
            if path0 == 0:
                assert sequencer.get("swap_paths") is False
            elif path0 == 1:
                assert sequencer.get("swap_paths") is True

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms(self, sequencer, pulse_bus_schedule: PulseBusSchedule, path0: int):
        """Unit tests for _generate_waveforms method"""
        label = pulse_bus_schedule.timeline[0].pulse.label()
        envelope = get_envelope()
        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule).to_dict()
        waveforms_keys = list(waveforms.keys())

        assert len(waveforms) == 2 * len(pulse_bus_schedule.timeline)
        assert waveforms_keys[0] == f"{label}_I"
        assert waveforms_keys[1] == f"{label}_Q"

        if path0 % 2 != 0:
            # swapped waveforms should have I component all zeros
            assert np.all(waveforms[waveforms_keys[0]]["data"]) == 0
            # swapped waveforms should have Q component equal to gaussian pulse envelope
            assert np.alltrue(envelope == waveforms[waveforms_keys[1]]["data"])
        else:
            # swapped waveforms should have Q component all zeros
            assert np.all(waveforms[waveforms_keys[1]]["data"]) == 0
            # swapped waveforms should have Q component equal to gaussian pulse envelope
            assert np.alltrue(envelope == waveforms[waveforms_keys[0]]["data"])

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms_multiple_pulses(
        self, sequencer, pulse_bus_schedule_repeated_pulses: PulseBusSchedule, path0: int
    ):
        """Unit tests for _generate_waveforms method with repeated pulses"""
        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule_repeated_pulses).to_dict()

        assert len(waveforms) == 2

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms_negative_amplitude(
        self, sequencer, pulse_bus_schedule_negative_amplitude: PulseBusSchedule, path0: int
    ):
        """Unit tests for _generate_waveforms method with negative amplitude"""
        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule_negative_amplitude).to_dict()

        assert isinstance(waveforms, dict)
        assert isinstance(str(waveforms), str)
        assert len(waveforms) == 2

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._generate_waveforms")
    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._generate_program")
    def test_translate_pulse_bus_schedule(
        self, mock_generate_program: MagicMock, mock_generate_waveforms: MagicMock, pulse_bus_schedule: PulseBusSchedule
    ):
        """Unit tests for _translate_pulse_bus_schedule method"""
        sequencer_name = "test_sequencer_translate_pulse_bus_schedule"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequence = sequencer._translate_pulse_bus_schedule(
            pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1
        )

        assert isinstance(sequence, QpySequence)
        mock_generate_waveforms.assert_called_once()
        mock_generate_program.assert_called_once()

    @pytest.mark.parametrize(
        "pulse_bus_schedule, name, expected_program_str",
        [
            (get_pulse_bus_schedule(START_TIME_DEFAULT), "0", expected_program_str_0),
            (get_pulse_bus_schedule(START_TIME_NON_ZERO), "1", expected_program_str_1),
        ],
    )
    def test_generate_program(self, pulse_bus_schedule: PulseBusSchedule, name: str, expected_program_str: str):
        """Unit tests for _generate_program method"""

        sequencer_name = f"test_sequencer_program{name}"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule)
        program = sequencer._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, nshots=1, repetition_duration=1000, num_bins=1
        )
        assert isinstance(program, Program)
        # assert is_q1asm_equal(program, expected_program_str)

    def test_execute(self, pulse_bus_schedule: PulseBusSchedule):
        """Unit tests for execute method"""
        parent = MagicMock()
        sequencer = SequencerQCM(parent=parent, name="sequencer_execute", seq_idx=0)

        with patch(
            "qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._translate_pulse_bus_schedule"
        ) as mock_translate:
            with patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.set") as mock_set:
                sequencer.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1)
                mock_set.assert_called_once()
                mock_translate.assert_called_once()
                parent.arm_sequencer.assert_called_once_with(sequencer=sequencer.seq_idx)
                parent.start_sequencer.assert_called_once_with(sequencer=sequencer.seq_idx)

    def test_generate_weights(self, sequencer):
        """Test the ``_generate_weights`` method."""
        weights = sequencer._generate_weights()
        assert isinstance(weights, Weights)

        weights = weights.to_dict()
        # must be empty dictionary
        assert not weights

    def test_generate_acquisitions(self, sequencer):
        """Test the ``_generate_acquisitions`` method."""
        num_bins = 1
        acquisitions = sequencer._generate_acquisitions(num_bins=num_bins)

        assert isinstance(acquisitions, Acquisitions)

        acquisitions = acquisitions.to_dict()
        # must be empty dictionary
        assert not acquisitions

    def test_params(self, sequencer):
        """Unittest to test the params property."""
        assert sequencer.params == sequencer.parameters

    def test_alias(self, sequencer):
        """Unittest to test the alias property."""
        assert sequencer.alias == sequencer.name
