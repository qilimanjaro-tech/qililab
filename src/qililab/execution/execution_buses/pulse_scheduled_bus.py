"""Pulse Scheduled Bus class."""
from dataclasses import dataclass, field

from qililab.platform import Bus
from qililab.pulse import PulseBusSchedule
from qililab.result.result import Result
from qililab.system_control import ReadoutSystemControl, SimulatedSystemControl, SystemControl
from qililab.utils import Waveforms


@dataclass
class PulseScheduledBus:
    """Pulse Scheduled Bus class."""

    bus: Bus
    pulse_schedule: list[PulseBusSchedule] = field(default_factory=list)

    def generate_program_and_upload(self, idx: int, nshots: int, repetition_duration: int) -> None:
        """Translate the Pulse Bus Schedule to each AWG program and upload them

        Args:
            idx (int): index of the pulse schedule to compile and upload
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
        """
        self.system_control.generate_program_and_upload(  # pylint: disable=no-member
            pulse_bus_schedule=self.pulse_schedule[idx],
            nshots=nshots,
            repetition_duration=repetition_duration,
        )

    def run(self):
        """Run the given pulse sequence."""
        return self.system_control.run()  # pylint: disable=no-member

    def add_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """

        self.pulse_schedule.append(pulse_bus_schedule)

    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
        if not isinstance(self.system_control, (ReadoutSystemControl, SimulatedSystemControl)):
            raise ValueError(
                f"The bus {self.bus.alias} needs a readout system control to acquire the results. This bus "
                f"has a {self.system_control.name} instead."
            )
        return self.system_control.acquire_result()  # type: ignore  # pylint: disable=no-member

    def acquire_time(self, idx: int = 0) -> int:
        """Pulse Scheduled Bus 'acquire_time' property.

        Returns:
            int: Acquire time (in ns).
        """
        num_sequences = len(self.pulse_schedule)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_schedule list of length {num_sequences}")
        readout_schedule = self.pulse_schedule[idx]
        time = readout_schedule.timeline[-1].start
        if isinstance(self.system_control, ReadoutSystemControl):
            time += self.system_control.acquisition_delay_time
        return time

    def waveforms(self, resolution: float = 1.0, idx: int = 0) -> Waveforms:
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Object containing arrays of the I/Q amplitudes
            of the pulses applied on this bus.
        """
        num_sequences = len(self.pulse_schedule)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_sequences list of length {num_sequences}")
        return self.pulse_schedule[idx].waveforms(resolution=resolution)

    @property
    def port(self):
        """Pulse Scheduled Bus 'port' property

        Returns:
            int: Port where the bus is connected.
        """
        return self.bus.port

    @property
    def system_control(self) -> SystemControl:
        """Pulse Scheduled Bus 'system_control' property.

        Returns:
            SystemControl: bus.system_control
        """
        return self.bus.system_control

    @property
    def id_(self):
        """Pulse Scheduled Bus 'id_' property.

        Returns:
            int: bus.id_
        """
        return self.bus.id_
