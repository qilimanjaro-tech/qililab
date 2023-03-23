"""Tests for the ExecutionBuilder class."""
import pytest

from qililab.execution import EXECUTION_BUILDER
from qililab.platform import Platform
from qililab.pulse import Pulse, PulseSchedule


class TestExecutionBuilder:
    """Unit tests checking the ExecutoinBuilder attributes and methods."""

    def test_build_method(self, platform: Platform, pulse_schedule: PulseSchedule):
        """Test build method."""
        EXECUTION_BUILDER.build(platform=platform, pulse_schedules=[pulse_schedule])

    def test_build_method_with_wrong_pulse_bus_schedule(
        self, platform: Platform, pulse_schedule: PulseSchedule, pulse: Pulse
    ):
        """Test build method with wrong pulse sequence."""
        pulse_schedule.add(pulse=pulse, start_time=0, port=1234)
        with pytest.raises(ValueError):
            EXECUTION_BUILDER.build(platform=platform, pulse_schedules=[pulse_schedule])
