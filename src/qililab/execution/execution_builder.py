"""ExecutionBuilder class"""
from typing import Dict, List

from qililab.execution.bus_execution import BusExecution
from qililab.execution.buses_execution import BusesExecution
from qililab.execution.execution import Execution
from qililab.platform import Platform
from qililab.typings.enums import SystemControlSubcategory
from qililab.pulse import PulseSchedule
from qililab.utils import Singleton


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, pulse_schedule: List[PulseSchedule]) -> Execution:
        """Build Execution class.

        Returns:
            Execution: Execution object.
        """
        buses_execution = self._build_buses_execution(platform=platform, pulse_schedule_list=pulse_schedule)

        return Execution(buses_execution=buses_execution, platform=platform)

    def _build_buses_execution(self, platform: Platform, pulse_schedule_list: List[PulseSchedule]):
        """Loop over pulses in PulseSequence, classify them by bus index and instantiate a BusesExecution class.

        Returns:
            BusesExecution: BusesExecution object.
        """
        buses: Dict[int, BusExecution] = {}
        for pulse_schedule in pulse_schedule_list:
            for pulse_bus_schedule in pulse_schedule:
                port = pulse_bus_schedule.port
                bus_idx, bus = platform.get_bus(port=port)
                if bus is None:
                    raise ValueError(f"There is no bus connected to port {port}.")
                if bus_idx not in buses:
                    buses[bus_idx] = BusExecution(bus=bus, pulse_schedule=[pulse_bus_schedule])
                    continue
                buses[bus_idx].add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

        # TODO: This is a temporary fix to add a CW bus when present in the platform, without a pulse sequence
        bus_idx, bus = platform.get_bus_by_system_control_type(
            system_control_subcategory=SystemControlSubcategory.CW_SYSTEM_CONTROL
        )
        if bus is not None:
            buses[bus_idx] = BusExecution(bus=bus, pulse_sequences=[])

        return BusesExecution(buses=list(buses.values()), num_sequences=len(pulse_schedule_list))
