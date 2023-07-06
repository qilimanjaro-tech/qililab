"""Tests for the SequencerQRM class."""
# pylint: disable=protected-access
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.program import Program
from qpysequence.sequence import Sequence as QpySequence

from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.pulse import Pulse, PulseBusSchedule, Rectangular
from qililab.pulse.pulse_event import PulseEvent

PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Rectangular.name
NUM_SLOTS = 20
START_TIME_DEFAULT = 0
START_TIME_NON_ZERO = 4


def get_pulse_bus_schedule(start_time):
    pulse_shape = Rectangular()
    pulse = Pulse(
        amplitude=PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=start_time)

    return PulseBusSchedule(timeline=[pulse_event], port=0)


expected_program_str_0 = repr(
    "setup:\n    move             1, R0\n    wait_sync        4\n\naverage:\n    move             0, R1\n    bin:\n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        long_wait_1:\n            wait             996\n\n        add              R1, 1, R1\n        nop\n        jlt              R1, 1, @bin\n    loop             R0, @average\nstop:\n    stop\n\n"
)
expected_program_str_1 = repr(
    "setup:\n    move             1, R0\n    wait_sync        4\n\naverage:\n    move             0, R1\n    bin:\n        long_wait_2:\n            wait             4\n\n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        long_wait_3:\n            wait             992\n\n        add              R1, 1, R1\n        nop\n        jlt              R1, 1, @bin\n    loop             R0, @average\nstop:\n    stop\n\n"
)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    return get_pulse_bus_schedule(start_time=0)


class TestSequencerQRM:
    """Unit tests checking the Sequencer attributes and methods"""

    def test_init(self):
        """Unit tests for init method"""

        sequencer_name = "test_sequencer_init"
        seq_idx = 0
        sequencer = SequencerQRM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        assert sequencer.get("sequence_timeout") == 1
        assert sequencer.get("acquisition_timeout") == 1
        assert sequencer.get("weights_i") == []
        assert sequencer.get("weights_q") == []
        assert sequencer.get("weighed_acq_enabled") is False

    @pytest.mark.xfail
    @pytest.mark.parametrize(
        "pulse_bus_schedule, name, expected_program_str",
        [
            (get_pulse_bus_schedule(START_TIME_DEFAULT), "0", expected_program_str_0),
            (get_pulse_bus_schedule(START_TIME_NON_ZERO), "1", expected_program_str_1),
        ],
    )
    def test_generate_program(self, pulse_bus_schedule, name, expected_program_str):
        """Unit tests for _generate_program method"""
        sequencer_name = f"test_sequencer_program{name}"
        seq_idx = 0
        sequencer = SequencerQRM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule)
        program = sequencer._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, nshots=1, repetition_duration=1000, num_bins=1
        )

        assert isinstance(program, Program)
        assert repr(dedent(repr(program))) == expected_program_str

    def test_execute(self, pulse_bus_schedule):
        """Unit tests for execute method"""
        parent = MagicMock()
        sequencer = SequencerQRM(parent=parent, name="sequencer_execute", seq_idx=0)

        with patch(
            "qililab.drivers.instruments.qblox.sequencer_qrm.SequencerQRM._translate_pulse_bus_schedule"
        ) as mock_translate:
            with patch("qililab.drivers.instruments.qblox.sequencer_qrm.SequencerQRM.set") as mock_set:
                sequencer.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1)
                mock_set.assert_called_once()
                mock_translate.assert_called_once()
                parent.arm_sequencer.assert_called_once()
                parent.start_sequencer.assert_called_once()
