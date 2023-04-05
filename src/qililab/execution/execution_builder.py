"""ExecutionBuilder class"""
from typing import Dict, List

from qililab.execution import BusExecution, Execution
from qililab.execution.execution_manager import ExecutionManager
from qililab.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, pulse_schedules: List[PulseSchedule]) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """

        return Execution(
            execution_manager=self._build_execution_manager(platform=platform, pulse_schedules=pulse_schedules),
            platform=platform,
        )

    def _build_execution_manager(self, platform: Platform, pulse_schedules: List[PulseSchedule]):
        """Loop over pulses in PulseSequence, classify them by bus index and instantiate a BusExecution class.

        Returns:
            ExecutionManager: ExecutionManager object.
        """
        buses: Dict[int, BusExecution] = {}
        for pulse_schedule in pulse_schedules:
            for pulse_bus_schedule in pulse_schedule.elements:
                port, bus_idx, bus = self._get_bus_info_from_pulse_bus_schedule_port(platform, pulse_bus_schedule)
                if bus is None:
                    raise ValueError(f"There is no bus connected to port {port}.")
                if bus_idx not in buses:
                    buses[bus_idx] = BusExecution(bus=bus, pulse_schedule=[pulse_bus_schedule])
                    continue
                buses[bus_idx].add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

        return ExecutionManager(buses=list(buses.values()), num_schedules=len(pulse_schedules))

    def _get_bus_info_from_pulse_bus_schedule_port(self, platform: Platform, pulse_bus_schedule: PulseBusSchedule):
        """get the bus information that it is connected to the port in the pulse bus schedule"""
        port = pulse_bus_schedule.port
        bus_idx, bus = platform.get_bus(port=port)
        return port, bus_idx, bus
