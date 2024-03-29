"""Tests for the ExecutionBuilder class."""
import copy
from warnings import catch_warnings

import numpy as np
import pytest

from qililab.circuit_transpiler import CircuitTranspiler
from qililab.constants import RUNCARD
from qililab.execution import EXECUTION_BUILDER, BusExecution
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseEvent, PulseSchedule
from qililab.typings import Parameter
from qililab.utils import Loop
from tests.data import Galadriel, circuit, experiment_params
from tests.test_utils import build_platform


@pytest.fixture(name="pulse_event")
def fixture_pulse_event() -> PulseEvent:
    """Load PulseEvent.

    Returns:
        PulseEvent: Instance of the PulseEvent class.
    """
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    return PulseEvent(pulse=pulse, start_time=0)


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="pulse_schedule", params=experiment_params)
def fixture_pulse_schedule(platform: Platform) -> PulseSchedule:
    """Return PulseSchedule instance."""
    return CircuitTranspiler(platform=platform).circuit_to_pulses(circuits=[circuit])[0]


@pytest.fixture(name="loops")
def fixture_loop() -> list[Loop]:
    """Return list of loops with alias equal to the alias in the Galadriel object specifyied in the data.py file"""
    return [
        Loop(alias=bus[RUNCARD.ALIAS], parameter=Parameter.CURRENT, values=np.linspace(0, 10, 10))
        for bus in copy.deepcopy(Galadriel.buses)
    ]


@pytest.fixture(name="nested_loops")
def fixture_nested_loop() -> list[Loop]:
    """Return list of a loop that contain nested loops with alias equal to the alias in the Galadriel object specifyied in the data.py file"""
    loops = [
        Loop(alias=bus[RUNCARD.ALIAS], parameter=Parameter.CURRENT, values=np.linspace(0, 10, 10))
        for bus in copy.deepcopy(Galadriel.buses)
    ]
    nested_loops = None
    for loop in reversed(loops):
        loop.loop = nested_loops
        nested_loops = loop

    return [nested_loops]


class TestExecutionBuilder:
    """Unit tests checking the ExecutoinBuilder attributes and methods."""

    def test_build_method(self, platform: Platform, pulse_schedule: PulseSchedule):
        """Test build method."""
        platform_bus_executions = []
        for pulse_bus_schedule in pulse_schedule.elements:
            bus = platform.buses.get(pulse_bus_schedule.port)
            platform_bus_executions.append(BusExecution(bus=bus, pulse_bus_schedules=[pulse_bus_schedule]))

        execution_manager = EXECUTION_BUILDER.build(platform=platform, pulse_schedules=[pulse_schedule])

        assert execution_manager.num_schedules == 1
        assert execution_manager.buses == platform_bus_executions

    def test_build_method_with_wrong_pulse_bus_schedule(
        self, platform: Platform, pulse_schedule: PulseSchedule, pulse_event: PulseEvent
    ):
        """Test build method with wrong pulse sequence."""
        test_port = "qubit_1000"
        delay = 0
        pulse_schedule.add_event(pulse_event=pulse_event, port=test_port, port_delay=delay)
        with pytest.raises(
            ValueError,
            match=f"There can only be one bus connected to a port. There are 0 buses connected to port {test_port}.",
        ):
            EXECUTION_BUILDER.build(platform=platform, pulse_schedules=[pulse_schedule])

    def test_build_from_loops_method(self, platform: Platform, loops: list[Loop]):
        """Test build_from_loops method"""
        loops_alias = [loop.alias for loop in loops]
        platform_bus_executions = [
            BusExecution(bus=bus, pulse_bus_schedules=[]) for bus in platform.buses if bus.alias in loops_alias
        ]

        with catch_warnings(record=True) as w:
            execution_manager = EXECUTION_BUILDER.build_from_loops(platform=platform, loops=loops)
            assert len(w) == 1  # One warning is always thrown at the begining
            assert execution_manager.num_schedules == 0
            assert execution_manager.buses == platform_bus_executions

    def test_build_from_loops_method_nested_loops(self, platform: Platform, nested_loops: list[Loop]):
        """Test build_from_loops method"""
        loops_alias = []
        for loops in nested_loops:
            for loop in loops.loops:
                loops_alias.append(loop.alias)
        platform_bus_executions = [
            BusExecution(bus=bus, pulse_bus_schedules=[]) for bus in platform.buses if bus.alias in loops_alias
        ]

        with catch_warnings(record=True) as w:
            execution_manager = EXECUTION_BUILDER.build_from_loops(platform=platform, loops=nested_loops)
            assert len(w) == 1  # One warning is always thrown at the begining
            assert execution_manager.num_schedules == 0
            assert execution_manager.buses == platform_bus_executions

    def test_build_from_loops_method_repeated_alias(self, platform: Platform, loops: list[Loop]):
        """Test build_from_loops method when two loops have the same alias"""
        loops_alias = [loop.alias for loop in loops]
        platform_bus_executions = [
            BusExecution(bus=bus, pulse_bus_schedules=[]) for bus in platform.buses if bus.alias in loops_alias
        ]

        loops.append(loops[-1])  # Repeat last alias to check for warning
        with catch_warnings(record=True) as w:
            execution_manager = EXECUTION_BUILDER.build_from_loops(platform=platform, loops=loops)
            assert len(w) == 2  # Two warnings should be thrown: Beggining and repeated alias
            assert execution_manager.num_schedules == 0
            assert execution_manager.buses == platform_bus_executions

    def test_build_method_from_loops_with_wrong_loop_alias(self, platform: Platform, loops: list[Loop]):
        """Test build_from_loops method raises an exception with a loop whose alias does not match any bus alias"""
        wrong_alias = "foobar"
        loop_with_wrong_alias = Loop(alias=wrong_alias, parameter=Parameter.CURRENT, values=np.linspace(0, 10, 10))
        loops_wrong = loops + [loop_with_wrong_alias]

        with pytest.raises(
            ValueError,
            match=f"There is no bus with alias: {wrong_alias}\n|INFO| Make sure the loop alias matches the bus alias specified in the runcard",
        ):
            EXECUTION_BUILDER.build_from_loops(platform=platform, loops=loops_wrong)
