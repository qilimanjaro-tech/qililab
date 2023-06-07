"""BusExecution class."""
from dataclasses import dataclass, field

from qililab.platform import Bus
from qililab.pulse import PulseBusSchedule
from qililab.result.result import Result
from qililab.system_control import ReadoutSystemControl, SimulatedSystemControl, SystemControl
from qililab.utils import Waveforms


@dataclass
class BusExecution:
    """This class contains the information of a specific bus in the platform together with a list of
    pulse schedules that will be executed on this bus."""

    bus: Bus
    pulse_bus_schedules: list[PulseBusSchedule] = field(default_factory=list)

    def compile(self, idx: int, nshots: int, repetition_duration: int, num_bins: int) -> list:
        """Compiles the pulse schedule at index ``idx`` into an assembly program.

        Args:
            idx (int): index of the circuit to compile and upload
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            num_bins (int): number of bins.

        Returns:
            list: list of compiled assembly programs
        """
        return self.system_control.compile(
            pulse_bus_schedule=self.pulse_bus_schedules[idx],
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )

    def upload(self):
        """Uploads any previously compiled program into the instrument."""
        self.system_control.upload()

    def run(self):
        """Run the given pulse sequence."""
        return self.system_control.run()

    def setup(self):
        """Generates the sequence for each bus and uploads it to the sequencer"""

    def add_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """

        self.pulse_bus_schedules.append(pulse_bus_schedule)

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
    def port(self):
        """BusExecution 'port' property

        Returns:
            int: Port where the bus is connected.
        """
        return self.bus.port

    @property
    def system_control(self) -> SystemControl:
        """BusExecution 'system_control' property.

        Returns:
            SystemControl: bus.system_control
        """
        return self.bus.system_control

    @property
    def id_(self):
        """BusExecution 'id_' property.

        Returns:
            int: bus.id_
        """
        return self.bus.id_

    @property
    def alias(self):
        """BusExecution 'alias' property.

        Returns:
            str: alias of the bus
        """
        return self.bus.alias
