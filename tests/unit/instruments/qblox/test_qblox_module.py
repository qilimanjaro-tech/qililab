"""Tests for the Qblox Module class."""
import copy

import numpy as np
import pytest
from qpysequence.program import Loop, Register
from qpysequence.utils.constants import AWG_MAX_GAIN

from qililab.instruments.awg_settings import AWGSequencer
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from tests.data import Galadriel


class DummyQbloxModule(QbloxModule):
    """Dummy QbloxModule class for testing"""

    def _generate_weights(self, sequencer: int) -> dict:
        return {}

    def _append_acquire_instruction(self, loop: Loop, bin_index: Register, sequencer_id: int):
        """Append an acquire instruction to the loop."""


@pytest.fixture(name="qblox_module")
def fixture_qblox_module():
    """Return an instance of QbloxModule class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return DummyQbloxModule(settings=settings)


@pytest.fixture(name="sequencer")
def fixture_sequencer():
    """Load simple sequencer

    Returns:
        PulseBusSchedule: Simple PulseBusSchedule
    """
    settings = {
        "identifier": 0,
        "chip_port_id": 1,
        "output_i": 0,
        "output_q": 1,
        "intermediate_frequency": 20000000,
        "gain_i": 0.001,
        "gain_q": 0.02,
        "gain_imbalance": 1,
        "phase_imbalance": 0,
        "offset_i": 0,
        "offset_q": 0,
        "hardware_modulation": True,
    }
    return AWGSequencer(**settings)


class TestQbloxModule:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_amp_phase_modification(self, qblox_module: QbloxModule):
        """Test amplification modification of a sequencer"""

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

        settings = awg_settings()
        sequencer = AWGSequencer(**settings)

        pulse_bus_schedule = PulseBusSchedule(timeline=timeline, port=0), amplitude, phase

        waveforms = qblox_module._generate_waveforms(
            pulse_bus_schedule[0], sequencer
        )  # pylint: disable=protected-access
        program = qblox_module._generate_program(
            pulse_bus_schedule=pulse_bus_schedule[0],
            waveforms=waveforms,
            sequencer=0,
        )  # pylint: disable=protected-access

        expected_gain = int(pulse_bus_schedule[1] * AWG_MAX_GAIN)
        expected_phase = int((pulse_bus_schedule[2] % 360) * 1e9 / 360)

        assert program.blocks[1].components[1].args[0] == expected_gain
        assert program.blocks[1].components[1].args[1] == expected_gain
        assert program.blocks[1].components[2].args[0] == expected_phase
