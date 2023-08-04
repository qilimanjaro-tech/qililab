from abc import abstractmethod

from qililab.pulse import PulseBusSchedule

from .base_instrument import BaseInstrument


class AWG(BaseInstrument):
    """
    Interface for AWG sequencer instrument types.
    """
    @abstractmethod
    def execute(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> None:
        """Compiles a pulse bus schedule, generates associated QASM program and runs it.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
