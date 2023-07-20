"""Tests for the SequencerQRM class."""
# pylint: disable=protected-access
import re
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.weights import Weights

from qililab.drivers.instruments.qblox.sequencer_qrm import SequencerQRM
from qililab.pulse import Pulse, PulseBusSchedule, Rectangular
from qililab.pulse.pulse_event import PulseEvent
from qililab.result.qblox_results import QbloxResult

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


expected_program_str_0 = r"setup:\n    move             0, R0\n    move             1, R1\n    move             1, R2\n    wait_sync        4\n    \naverage:\n    move             0, R3\n    bin:\n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        acquire          0, R3, 4\n        long_wait_\d+:\n            wait             992\n            \n        add              R3, 1, R3\n        nop\n        jlt              R3, 1, @bin\n    loop             R2, @average\nstop:\n    stop\n    \n"

expected_program_str_1 = r"setup:\n    move             0, R0\n    move             1, R1\n    move             1, R2\n    wait_sync        4\n    \naverage:\n    move             0, R3\n    bin:\n        long_wait_\d+:\n            wait             4\n            \n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        acquire          0, R3, 4\n        long_wait_\d+:\n            wait             988\n            \n        add              R3, 1, R3\n        nop\n        jlt              R3, 1, @bin\n    loop             R2, @average\nstop:\n    stop\n    \n"


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

    def test_get_results(self):
        """Unit test for the ``get_results`` method."""
        seq_idx = 1
        sequence_timeout = 4
        acquisition_timeout = 6
        parent = MagicMock()
        sequencer = SequencerQRM(parent=parent, name="test", seq_idx=seq_idx)

        # Set test values
        sequencer.set("sequence_timeout", sequence_timeout)
        sequencer.set("acquisition_timeout", acquisition_timeout)

        # Get results
        with patch.object(QbloxResult, "__post_init__") as post_init:
            results = sequencer.get_results()
            post_init.assert_called_once_with()

        # Assert calls and results
        parent.get_sequencer_state.assert_called_once_with(sequencer=seq_idx, timeout=sequence_timeout)
        parent.get_acquisition_state.assert_called_once_with(sequencer=seq_idx, timeout=acquisition_timeout)
        parent.store_scope_acquisition.assert_not_called()
        parent.get_acquisitions(sequencer=seq_idx)
        # assert sequencer.get("sync_en") is False  # TODO: Uncomment this once qblox dummy driver is fixed
        assert results.integration_lengths == [sequencer.get("integration_length_acq")]

    def test_get_results_with_weights(self):
        """Test that calling ``get_results`` with a weighed acquisition, the integration length
        corresponds to the length of the weights' list."""
        sequencer = SequencerQRM(parent=MagicMock(), name="test", seq_idx=4)

        # Set values
        sequencer.set("weights_i", [1, 2, 3, 4, 5])
        sequencer.set("weights_q", [6, 7, 8, 9, 10])
        sequencer.set("weighed_acq_enabled", True)

        # Get results
        with patch.object(QbloxResult, "__post_init__") as post_init:
            results = sequencer.get_results()
            post_init.assert_called_once_with()

        # Asserts
        assert results.integration_lengths == [len(sequencer.get("weights_i"))]

    def test_get_results_with_scope_acquisition(self):
        """Test calling ``get_results`` when scope acquisition is enabled."""
        seq_idx = 4
        parent = MagicMock()
        parent.get.return_value = seq_idx
        sequencer = SequencerQRM(parent=parent, name="test", seq_idx=seq_idx)

        # Execute and get results
        with patch.object(QbloxResult, "__post_init__") as post_init:
            _ = sequencer.get_results()
            post_init.assert_called_once_with()

        # Asserts
        parent.store_scope_acquisition.assert_called_once_with(sequencer=seq_idx, name="default")

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
        assert re.match(expected_program_str, repr(program))

    def test_generate_empty_weights(self):
        """Test the ``_generate_weights`` method when no weights have been set beforehand."""
        sequencer = SequencerQRM(parent=MagicMock(), name="test", seq_idx=4)

        weights = sequencer._generate_weights()
        assert isinstance(weights, Weights)

        weights = weights.to_dict()
        # must be empty dictionary
        assert not weights

        # Set values only for channel i
        weights_i = [1, 2, 3, 4]
        sequencer.set("weights_i", weights_i)
        weights = sequencer._generate_weights().to_dict()

        # must be empty dictionary
        assert not weights

        # Set values only for channel q
        weights_q = [1, 2, 3, 4]
        sequencer.set("weights_i", [])
        sequencer.set("weights_q", weights_q)
        weights = sequencer._generate_weights().to_dict()

        # must be empty dictionary
        assert not weights

    def test_generate_weights(self):
        """Test the ``_generate_weights`` method."""
        sequencer = SequencerQRM(parent=MagicMock(), name="test", seq_idx=4)

        # Set values
        weights_i = [1, 2, 3, 4]
        weights_q = [5, 6, 7, 8]
        sequencer.set("weights_i", weights_i)
        sequencer.set("weights_q", weights_q)

        weights = sequencer._generate_weights()

        assert len(weights._weight_pairs) == 1
        pair = weights._weight_pairs[0]
        assert pair.weight_i.data == weights_i
        assert pair.weight_q.data == weights_q

    def test_generate_acquisitions(self):
        """Test the ``_generate_acquisitions`` method."""
        sequencer = SequencerQRM(parent=MagicMock(), name="test", seq_idx=4)
        num_bins = 1
        acquisitions = sequencer._generate_acquisitions(num_bins=num_bins)
        acquisitions_dict = acquisitions.to_dict()

        assert isinstance(acquisitions, Acquisitions)
        assert "default" in acquisitions_dict
        default_acq = acquisitions_dict["default"]

        assert "num_bins" in default_acq
        assert default_acq["num_bins"] == num_bins

    def test_generate_weights_with_swap(self):
        """Test the ``_generate_weights`` method when `swap_paths` is True."""
        sequencer = SequencerQRM(parent=MagicMock(), name="test", seq_idx=4)

        # Set values
        weights_i = [1, 2, 3, 4]
        weights_q = [5, 6, 7, 8]
        sequencer.set("weights_i", weights_i)
        sequencer.set("weights_q", weights_q)
        sequencer.set("swap_paths", True)

        weights = sequencer._generate_weights()

        assert len(weights._weight_pairs) == 1
        pair = weights._weight_pairs[0]
        assert pair.weight_i.data == weights_q
        assert pair.weight_q.data == weights_i

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
