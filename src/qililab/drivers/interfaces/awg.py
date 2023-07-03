from abc import ABC, abstractmethod
from typing import Any

from qililab.pulse import PulseBusSchedule


class AWG:
    """
    Interface for AWG sequencer instrument types.
    """

    @abstractmethod
    def set(self, param_name: str, param_value: Any) -> None:
        """Set parameter on the instrument.

        Args:
            param (str): Parameter's name.
            value (float): Parameter's value
        """

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Return value associated to a parameter on the instrument.

        Args:
            param (str): Parameter's name.
        Returns:
            value (float): Parameter's value
        """

    @abstractmethod
    def execute(
        self,
        pulse_bus_schedule: PulseBusSchedule,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
        min_wait_time: int,
    ) -> None:
        """Compiles a pulse bus schedule, generates associated QASM program and runs it.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
