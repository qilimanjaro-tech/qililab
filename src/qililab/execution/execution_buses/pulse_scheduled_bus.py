"""Pulse Scheduled Bus class."""
from dataclasses import dataclass, field
from pathlib import Path

from qililab.platform.components.bus_types import SimulatedBus, TimeDomainBus
from qililab.pulse import PulseBusSchedule
from qililab.system_controls.system_control_types import (
    SimulatedSystemControl,
    TimeDomainSystemControl,
)
from qililab.typings import BusSubCategory
from qililab.utils import Waveforms


@dataclass
class PulseScheduledBus:
    """Pulse Scheduled Bus class."""

    bus: TimeDomainBus | SimulatedBus
    pulse_schedule: list[PulseBusSchedule] = field(default_factory=list)

    def generate_program_and_upload(
        self, schedule_index_to_load: int, nshots: int, repetition_duration: int, path: Path
    ) -> None:
        """Translate the Pulse Bus Schedule to each AWG program and upload them

        Args:
            schedule_index_to_load (int): specific schedule to load
            nshots (int): number of shots / hardware average
            repetition_duration (int): maximum window for the duration of one hardware repetition
            path (Path): path to save the program to upload
        """
        self.system_control.generate_program_and_upload(  # pylint: disable=no-member
            pulse_bus_schedule=self.pulse_schedule[schedule_index_to_load],
            nshots=nshots,
            repetition_duration=repetition_duration,
            path=path,
        )

    def run(self):
        """Run the given pulse sequence."""
        return self.system_control.run()  # pylint: disable=no-member

    def setup(self):
        """Generates the sequence for each bus and uploads it to the sequencer"""
        return self.system_control.setup()

    def add_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """

        self.pulse_schedule.append(pulse_bus_schedule)

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
        return self.pulse_schedule[idx].waveforms(frequency=self.bus.frequency, resolution=resolution)

    @property
    def port(self):
        """Pulse Scheduled Bus 'port' property

        Returns:
            int: Port where the bus is connected.
        """
        return self.bus.port

    @property
    def system_control(self) -> TimeDomainSystemControl | SimulatedSystemControl:
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

    @property
    def bus_subcategory(self) -> BusSubCategory:
        """Pulse Scheduled Bus 'subcategory' property.

        Returns:
            BusSubCategory: Bus subcategory.
        """
        return self.bus.bus_subcategory
