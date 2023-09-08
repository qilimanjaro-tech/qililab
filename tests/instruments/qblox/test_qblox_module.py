"""Tests for the Qblox Module class."""
import copy

import numpy as np
import pytest
from qpysequence.program import Loop, Register
from qpysequence.utils.constants import AWG_MAX_GAIN
from qpysequence.weights import Weights

from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from tests.data import Galadriel


class DummyQbloxModule(QbloxModule):
    """Dummy QbloxModule class for testing"""

    def _generate_weights(self, sequencer: AWGQbloxSequencer):  # pylint: disable=unused-argument
        return Weights()

    def _append_acquire_instruction(  # pylint: disable=unused-argument
        self, loop: Loop, bin_index: Register, sequencer_id: int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""


@pytest.fixture(name="qblox_module")
def fixture_qblox_module():
    """Return an instance of QbloxModule class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return DummyQbloxModule(settings=settings)


class TestQbloxModule:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_amplitude_and_phase_in_program(self, qblox_module: QbloxModule):
        """Test that the amplitude and the phase of a compiled pulse is added into the Qblox program."""

        amplitude = 0.8
        phase = np.pi / 2 + 12.2
        timeline = [
            PulseEvent(
                pulse=Pulse(
                    amplitude=amplitude,
                    phase=phase,
                    duration=1000,
                    frequency=7.0e9,
                    pulse_shape=Gaussian(num_sigmas=5),
                ),
                start_time=0,
            )
        ]

        pulse_bus_schedule = PulseBusSchedule(timeline=timeline, port="drive_q0")

        sequences = qblox_module.compile(pulse_bus_schedule, nshots=1, repetition_duration=1, num_bins=1)
        program = sequences[0]._program

        expected_gain = int(amplitude * AWG_MAX_GAIN)
        expected_phase = int((phase % (2 * np.pi)) * 1e9 / (2 * np.pi))

        bin_loop = program.blocks[1].components[1]

        assert bin_loop.components[1].args[0] == expected_gain
        assert bin_loop.components[1].args[1] == expected_gain
        assert bin_loop.components[2].args[0] == expected_phase