"""Simulated Pulse Scheduled Bus class."""
from dataclasses import dataclass, field

from qililab.execution.execution_buses.pulse_scheduled_readout_bus import PulseScheduledReadoutBus
from qililab.platform.components.bus_types import SimulatedBus
from qililab.pulse import PulseBusSchedule
from qililab.result.result import Result
from qililab.system_controls.system_control_types import SimulatedSystemControl


@dataclass
class SimulatedPulseScheduledReadoutBus(PulseScheduledReadoutBus):
    """Simulated Pulse Scheduled Readout Bus class."""

    bus: SimulatedBus
    pulse_schedule: list[PulseBusSchedule] = field(default_factory=list)

    @property
    def system_control(self) -> SimulatedSystemControl:
        """Pulse Scheduled Bus 'system_control' property.

        Returns:
            SystemControl: bus.system_control
        """
        return self.bus.system_control

    def generate_program(self, idx: int) -> None:
        """For each Bus (with a pulse schedule), translate it to an AWG program and upload it

        Args:
            idx (int): index of the pulse schedule to compile and upload
        """
        self.system_control.generate_program(pulse_bus_schedule=self.pulse_schedule[idx])

    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
        return self.system_control.acquire_result()  # pylint: disable=no-member

    def acquire_time(self, idx: int = 0) -> int:
        """Pulse Scheduled Bus 'acquire_time' property.

        Returns:
            int: Acquire time (in ns).
        """
        num_sequences = len(self.pulse_schedule)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_schedule list of length {num_sequences}")
        readout_schedule = self.pulse_schedule[idx]
        return readout_schedule.timeline[-1].start
