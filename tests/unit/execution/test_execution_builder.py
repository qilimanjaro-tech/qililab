"""Tests for the ExecutionBuilder class."""
import pytest

from qililab.execution import EXECUTION_BUILDER
from qililab.platform import Platform
from qililab.pulse import Pulse, PulseSequences


class TestExecutionBuilder:
    """Unit tests checking the ExecutoinBuilder attributes and methods."""

    def test_build_method(self, platform: Platform, pulse_sequence: PulseSequences):
        """Test build method."""
        EXECUTION_BUILDER.build(platform=platform, pulse_sequences=[pulse_sequence])

    def test_build_method_with_wrong_pulse_sequence(
        self, platform: Platform, pulse_sequence: PulseSequences, pulse: Pulse
    ):
        """Test build method with wrong pulse sequence."""
        pulse.qubit_ids = [3, 4, 9, 12]  # mess up qubit_ids
        pulse_sequence.add(pulse=pulse)
        with pytest.raises(ValueError):
            EXECUTION_BUILDER.build(platform=platform, pulse_sequences=[pulse_sequence])
