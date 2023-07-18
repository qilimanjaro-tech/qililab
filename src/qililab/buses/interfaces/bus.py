"""Bus Class Interface."""
from abc import ABC, abstractmethod
from qcodes import Instrument
from typing import Any

from qililab.pulse import PulseBusSchedule

class BusInterface(ABC):
    """Interface of a Bus."""

    def __init__(self):
        """Initialise the bus."""
        self.submodules: dict[str, ABC] = {}

    @abstractmethod
    def execute(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> None:
        """Execute a pulse bus schedule through an AWG Sequencer belonging to the bus.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """

    @abstractmethod
    def add_submodule(
        self, name: str, submodule: ABC
    ) -> None:
        """
        Bind one submodule to this bus.

        Instrument subclasses can call this repeatedly in their ``__init__``
        method for every submodule of the instrument.

        Args:
            name: How the submodule will be stored within
                bus and also how it can be
                addressed.
            submodule: The submodule to be stored.

        Raises:
            KeyError: If this instrument already contains a submodule with this
                name.
        """
        if name in self.submodules:
            raise KeyError(f"Duplicate submodule name {name}")
        self.submodules[name] = submodule

    @abstractmethod
    def set_parameter(self, instrument_name: str, param_name: str, value: Any) -> None:
        """Set parameter on the bus' instruments.

        Args:
            instrument_name (str): Name of the instrument to set parameter
            param (str): Parameter's name.
            value (float): Parameter's value
        """

    @abstractmethod
    def get_parameter(self, instrument_name: str, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            instrument_name (str): Name of the instrument to get parameter
            param (str): Parameter's name.
        Returns:
            value (float): Parameter's value
        """
