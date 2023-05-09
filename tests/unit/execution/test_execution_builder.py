"""Tests for the ExecutionBuilder class."""
from typing import List

import numpy as np
import pytest

from qililab.constants import RUNCARD
from qililab.execution import EXECUTION_BUILDER, BusExecution
from qililab.execution.execution_manager import ExecutionManager
from qililab.platform import Platform
from qililab.pulse import PulseEvent, PulseSchedule
from qililab.typings import Parameter
from qililab.utils import Loop
from tests.data import Galadriel


@pytest.fixture(name="loops")
def fixture_loop() -> List[Loop]:
    """Return list of loops with alias equal to the alias in the Galadriel object specifyied in the data.py file"""
    return [
        Loop(alias=bus[RUNCARD.ALIAS], parameter=Parameter.CURRENT, values=np.linspace(0, 10, 10))
        for bus in Galadriel.buses
    ]


class TestExecutionBuilder:
    """Unit tests checking the ExecutoinBuilder attributes and methods."""

    def test_build_method(self, platform: Platform, pulse_schedule: PulseSchedule):
        """Test build method."""
        platform_bus_executions = []
        for pulse_bus_schedule in pulse_schedule.elements:
            _, bus = platform.get_bus(pulse_bus_schedule.port)
            platform_bus_executions.append(BusExecution(bus=bus, pulse_schedule=[pulse_bus_schedule]))

        expected = ExecutionManager(buses=platform_bus_executions, num_schedules=1, platform=platform)
        execution_manager = EXECUTION_BUILDER.build(platform=platform, pulse_schedules=[pulse_schedule])

        assert execution_manager == expected

    def test_build_method_with_wrong_pulse_bus_schedule(
        self, platform: Platform, pulse_schedule: PulseSchedule, pulse_event: PulseEvent
    ):
        """Test build method with wrong pulse sequence."""
        test_port = 1234
        pulse_schedule.add_event(pulse_event=pulse_event, port=test_port)
        with pytest.raises(ValueError, match=f"There is no bus connected to port {test_port}."):
            EXECUTION_BUILDER.build(platform=platform, pulse_schedules=[pulse_schedule])

    def test_build_from_loops_method(self, platform: Platform, loops: List[Loop]):
        """Test build_from_loops method"""
        loops_alias = [loop.alias for loop in loops]
        platform_bus_executions = [
            BusExecution(bus=bus, pulse_schedule=[]) for bus in platform.buses if bus.alias in loops_alias
        ]
        expected = ExecutionManager(buses=platform_bus_executions, num_schedules=0, platform=platform)

        loops.append(loops_alias[-1])  # Repeat last alias to check for warning
        execution_manager = EXECUTION_BUILDER.build_from_loops(platform=platform, loops=loops)

        assert execution_manager == expected

    def test_build_method_from_loops_with_wrong_loop_alias(self, platform: Platform, loops: List[Loop]):
        """Test build_from_loops method raises an exception with a loop whose alias does not match any bus alias"""
        wrong_alias = "foobar"
        loop_with_wrong_alias = Loop(alias=wrong_alias, parameter=Parameter.CURRENT, values=np.linspace(0, 10, 10))
        loops_wrong = loops + [loop_with_wrong_alias]

        with pytest.raises(
            ValueError,
            match=f"There is no bus with alias: {wrong_alias}\n|INFO| Make sure the loop alias matches the bus alias specified in the runcard",
        ):
            EXECUTION_BUILDER.build_from_loops(platform=platform, loops=loops_wrong)
