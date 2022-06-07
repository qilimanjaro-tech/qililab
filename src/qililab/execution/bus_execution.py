"""BusExecution class."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from qililab.platform import Bus
from qililab.pulse import Pulse, PulseSequence


@dataclass
class BusExecution:
    """BusExecution class."""

    bus: Bus
    pulse_sequences: List[PulseSequence] = field(default_factory=list)

    def connect(self):
        """Connect to the instruments."""
        self.system_control.connect()
        if self.attenuator is not None:
            self.attenuator.connect()

    def setup(self):
        """Setup instruments."""
        self.system_control.setup()
        if self.attenuator is not None:
            self.attenuator.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.system_control.start()

    def run(self, nshots: int, repetition_duration: int, idx: int, path: Path):
        """Run the given pulse sequence."""
        return self.system_control.run(
            pulse_sequence=self.pulse_sequences[idx], nshots=nshots, repetition_duration=repetition_duration, path=path
        )

    def close(self):
        """Close connection to the instruments."""
        self.system_control.close()

    def add_pulse(self, pulse: Pulse, idx: int):
        """Add pulse to the BusPulseSequence given by idx.

        Args:
            pulse (Pulse): Pulse object.
            idx (int): Index of the BusPulseSequence to add the pulse.
        """
        if idx > len(self.pulse_sequences):
            raise ValueError("Bad index value.")
        if idx == len(self.pulse_sequences):
            self.pulse_sequences.append(PulseSequence(qubit_ids=pulse.qubit_ids, pulses=[pulse]))
        else:
            self.pulse_sequences[idx].add(pulse)

    def waveforms(self, resolution: float = 1.0):
        """Return pulses applied on this bus.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Tuple[List[float], List[float]]: Dictionary containing a list of the I/Q amplitudes
            of the pulses applied on this bus.
        """
        waveforms_i, waveforms_q = [], []
        for pulse_sequence in self.pulse_sequences:
            waveform_i, waveform_q = pulse_sequence.waveforms(
                frequency=self.system_control.frequency, resolution=resolution
            )
            waveforms_i += waveform_i
            waveforms_q += waveform_q
        return waveforms_i, waveforms_q

    @property
    def qubit_ids(self):
        """BusExecution 'qubit_ids' property

        Returns:
            int: ID of the qubit connected to the bus.
        """
        return self.bus.qubit_ids

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