"""Tests for the ExecutionBuilder class."""
import pytest

from qililab.execution import EXECUTION_BUILDER
from qililab.platform import Platform
from qililab.pulse import Pulse, Pulses


class TestExecutionBuilder:
    """Unit tests checking the ExecutoinBuilder attributes and methods."""

    def test_build_method(self, platform: Platform, pulses: Pulses):
        """Test build method."""
        EXECUTION_BUILDER.build(platform=platform, pulses_list=[pulses])

    def test_build_method_with_wrong_pulse_sequence(self, platform: Platform, pulses: Pulses, pulse: Pulse):
        """Test build method with wrong pulse sequence."""
        pulse.port = 1234  # mess up port
        pulses.add(pulse=pulse)
        with pytest.raises(ValueError):
            EXECUTION_BUILDER.build(platform=platform, pulses_list=[pulses])
