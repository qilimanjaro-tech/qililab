"""Tests for the Qblox Module class."""
import copy

import numpy as np
import pytest
from qpysequence.program import Loop, Register
from qpysequence.utils.constants import AWG_MAX_GAIN

from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from tests.data import Galadriel


class DummyQbloxModule(QbloxModule):
    """Dummy QbloxModule class for testing"""

    def _generate_weights(self, sequencer_id: int) -> dict:
        return {}

    def _append_acquire_instruction(self, loop: Loop, bin_index: Register, sequencer_id: int):
        """Append an acquire instruction to the loop."""


@pytest.fixture(name="qblox_module")
def fixture_qblox_module():
    """Return an instance of QbloxModule class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return DummyQbloxModule(settings=settings)


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule():
    """Load simple PulseBusSchedule

    Returns:
        PulseBusSchedule: Simple PulseBusSchedule
    """
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
    return PulseBusSchedule(timeline=timeline, port=0), amplitude, phase


class TestQbloxModule:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_amp_phase_modification(self, qblox_module: QbloxModule, pulse_bus_schedule):
        """Test amplification modification of a sequencer"""
        waveforms = qblox_module._generate_waveforms(pulse_bus_schedule[0])  # pylint: disable=protected-access
        program = qblox_module._generate_program(  # pylint: disable=protected-access
            pulse_bus_schedule=pulse_bus_schedule[0],
            waveforms=waveforms,
            sequencer=0,
        )

        expected_gain = int(pulse_bus_schedule[1] * AWG_MAX_GAIN)
        expected_phase = int((pulse_bus_schedule[2] % 360) * 1e9 / 360)

        assert program.blocks[1].components[1].args[0] == expected_gain
        assert program.blocks[1].components[1].args[1] == expected_gain
        assert program.blocks[1].components[2].args[0] == expected_phase
