"""BusExecution class."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from qililab.platform import Bus
from qililab.pulse import PulseSequence
from qililab.typings import BusSubcategory
from qililab.utils import Waveforms


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulse_sequences: List[PulseSequence] = field(default_factory=list)

    def setup(self):
        """Setup instruments."""
        self.system_control.setup(frequencies=self.bus.target_freqs)
        if self.attenuator is not None:
            self.attenuator.setup()

    def turn_on(self):
        """Start/Turn on the instruments."""
        self.system_control.turn_on()

    def run(self, nshots: int, repetition_duration: int, idx: int, path: Path):
        """Run the given pulse sequence."""
        if self.bus.target_freqs[0] != self.system_control.frequency:  # update freq if target_freq has changed
            self.system_control.frequency = self.bus.target_freqs
        return self.system_control.run(
            pulse_sequence=self.pulse_sequences[idx], nshots=nshots, repetition_duration=repetition_duration, path=path
        )

    def add_pulse_sequence(self, pulse_sequence: PulseSequence):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """

        self.pulse_sequences.append(pulse_sequence)

    def waveforms(self, resolution: float = 1.0, idx: int = 0) -> Waveforms:
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Waveforms: Object containing arrays of the I/Q amplitudes
            of the pulses applied on this bus.
        """
        num_sequences = len(self.pulse_sequences)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_sequences list of length {num_sequences}")
        return self.pulse_sequences[idx].waveforms(frequency=self.system_control.awg_frequency, resolution=resolution)

    @property
    def port(self):
        """BusExecution 'port' property

        Returns:
            int: Port where the bus is connected.
        """
        return self.bus.port

    @property
    def system_control(self):
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
    def attenuator(self):
        """BusExecution 'attenuator' property.

        Returns:
            SystemControl: bus.attenuator
        """
        return self.bus.attenuator

    @property
    def subcategory(self) -> BusSubcategory:
        """BusExecution 'subcategory' property.

        Returns:
            BusSubcategory: Bus subcategory.
        """
        return self.bus.subcategory

    def acquire_time(self, idx: int = 0) -> int:
        """BusExecution 'acquire_time' property.

        Returns:
            int: Acquire time (in ns).
        """
        num_sequences = len(self.pulse_sequences)
        if idx >= num_sequences:
            raise IndexError(f"Index {idx} is out of bounds for pulse_sequences list of length {num_sequences}")
        readout_pulse = self.pulse_sequences[idx]
        return readout_pulse.pulses[-1].start + self.system_control.acquisition_delay_time
