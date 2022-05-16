"""Test execution."""
from unittest.mock import MagicMock, patch

import pytest

from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.execution import Execution
from qililab.experiment import Experiment
from qililab.pulse import Pulse, PulseSequence, ReadoutPulse
from qililab.pulse.pulse_shape import Drag
from qililab.typings import Category

from ..utils.side_effect import yaml_safe_load_side_effect


@patch("qililab.settings.settings_manager.yaml.safe_load", return_value=yaml_safe_load_side_effect)
@pytest.fixture(name="experiment")
def fixture_experiment():
    """Return Experiment object."""
    pulse_sequence = PulseSequence()
    pulse_sequence.add(Pulse(amplitude=1, phase=0, pulse_shape=Drag(num_sigmas=4, beta=1), duration=50, qubit_ids=[0]))
    pulse_sequence.add(ReadoutPulse(amplitude=1, phase=0, duration=50, qubit_ids=[0]))

    return Experiment(platform_name=DEFAULT_PLATFORM_NAME, sequences=[pulse_sequence])


class TestExecution:
    """Unit tests checking the Execution attributes and methods"""
