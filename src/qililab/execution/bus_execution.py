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

"""BusExecution class."""
from dataclasses import dataclass, field

from qililab.platform import Bus
from qililab.pulse import PulseBusSchedule
from qililab.system_control import ReadoutSystemControl, SystemControl
from qililab.utils import Waveforms


# TODO: Remove class once a Drawer class is implemented
@dataclass
class BusExecution:
    """This class contains the information of a specific bus in the platform together with a list of
    pulse schedules that will be executed on this bus.

    This class is a relic and should be removed once the drawing responsibilities are moved to its own class.

    Args:
        bus (Bus): Bus where the pulse schedules will be executed.
        pulse_bus_schedules (list[PulseBusSchedule]): pulse schedules to execute on the Bus.
    """

    bus: Bus
    pulse_bus_schedules: list[PulseBusSchedule] = field(default_factory=list)

    def add_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """
        self.pulse_bus_schedules.append(pulse_bus_schedule)

    def acquire_time(self, idx: int = 0) -> int:
        """BusExecution 'acquire_time' property.

        Returns:
            int: Acquire time (in ns).
        """
        num_sequences = len(self.pulse_bus_schedules)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_schedule list of length {num_sequences}")
        readout_schedule = self.pulse_bus_schedules[idx]
        time = readout_schedule.timeline[-1].start_time
        if isinstance(self.system_control, ReadoutSystemControl):
            time += self.system_control.acquisition_delay_time
        return time

    def waveforms(self, modulation: bool = True, resolution: float = 1.0, idx: int = 0) -> Waveforms:
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Object containing arrays of the I/Q amplitudes
            of the pulses applied on this bus.
        """
        num_sequences = len(self.pulse_bus_schedules)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_sequences list of length {num_sequences}")
        return self.pulse_bus_schedules[idx].waveforms(modulation=modulation, resolution=resolution)

    @property
    def system_control(self) -> SystemControl:
        """BusExecution 'system_control' property.

        Returns:
            SystemControl: bus.system_control
        """
        return self.bus.system_control

    @property
    def alias(self):
        """BusExecution 'alias' property.

        Returns:
            str: alias of the bus
        """
        return self.bus.alias
