# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ExecutionBuilder class"""
from warnings import warn

from qililab.platform import Platform
from qililab.pulse import PulseSchedule
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.utils import Loop, Singleton

from .bus_execution import BusExecution
from .execution_manager import ExecutionManager


class ExecutionBuilder(metaclass=Singleton):
    """Builder of platform objects."""

    def build(self, platform: Platform, pulse_schedules: list[PulseSchedule]) -> ExecutionManager:
        """Build ExecutionManager class.
        Loop over pulses in PulseSequence, classify them by bus index and instantiate a BusExecution class.

        Returns:
            ExecutionManager: ExecutionManager object.
        """
        buses: dict[int, BusExecution] = {}
        for pulse_schedule in pulse_schedules:
            for pulse_bus_schedule in pulse_schedule.elements:
                port, bus = self._get_bus_info_from_pulse_bus_schedule_port(platform, pulse_bus_schedule)
                if port not in buses:
                    buses[port] = BusExecution(bus=bus, pulse_bus_schedules=[pulse_bus_schedule])
                    continue
                buses[port].add_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

        return ExecutionManager(buses=list(buses.values()), num_schedules=len(pulse_schedules))

    def build_from_loops(self, platform: Platform, loops: list[Loop]) -> ExecutionManager:
        """Build ExecutionManager class.
        Loop over loops, classify them by bus alias and instantiate a BusExecution class.

        Returns:
            ExecutionManager: ExecutionManager object.
        """
        warn(
            "|WARNING| Bus alias are not unique and can be repeated in the runcard\nThe first bus alias that matches the loop alias will be selected"
        )
        buses: dict[str, BusExecution] = {}
        for loop in loops:
            for _loop in loop.loops:  # Iterate over nested loops if any
                alias, bus = self._get_bus_info_from_loop_alias(platform, _loop)
                if bus is None:
                    raise ValueError(
                        f"There is no bus with alias '{alias}'\n|INFO| Make sure the loop alias matches the bus alias specified in the runcard"
                    )
                if alias in buses:
                    warn(
                        f"|WARNING| Loop alias is repeated\nBus execution for bus with alias '{alias}' already created, skipping iteration"
                    )
                else:
                    buses[alias] = BusExecution(bus=bus, pulse_bus_schedules=[])

        return ExecutionManager(buses=list(buses.values()), num_schedules=0)

    def _get_bus_info_from_pulse_bus_schedule_port(self, platform: Platform, pulse_bus_schedule: PulseBusSchedule):
        """get the bus information that it is connected to the port in the pulse bus schedule
        Args:
            platform: Platform
            pulse_bus_schedule: PulseBusSchedule
        Returns:
            port: pulse_bus_schedule.port
            bus_idx: index of the bus
            bus: Bus object
        """
        port = pulse_bus_schedule.port
        bus = platform.buses.get(port=port)
        return port, bus

    def _get_bus_info_from_loop_alias(self, platform: Platform, loop: Loop):
        """get the bus information that it is connected to the port from the loop alias. Loop alias has to be the same as the bus alias
        Args:
            platform: Platform
            loop: Loop
        Returns:
            alias: alias of the bus
            bus: Bus object
        """
        alias = loop.alias
        bus = platform._get_bus_by_alias(alias=alias)  # pylint: disable=protected-access
        return alias, bus
