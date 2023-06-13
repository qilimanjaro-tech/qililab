"""QubitControl class."""
from abc import abstractmethod

from qililab.constants import RUNCARD
from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule


class AWG(Instrument):
    """Abstract base class defining all instruments used to control or readout the qubits."""

    @abstractmethod
    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins

        Returns:
            list: list of compiled assembly programs
        """

    @abstractmethod
    def run(self, port: int):
        """Run the uploaded program"""

    @abstractmethod
    def upload(self, port: int):
        """Upload compiled program."""

    @property
    def num_sequencers(self):
        """Number of sequencers in the AWG

        Returns:
            int: number of sequencers
        """
        return self.settings.num_sequencers

    def to_dict(self):
        """Return a dict representation of an AWG instrument."""
        return {RUNCARD.NAME: self.name.value} | self.settings.to_dict()
