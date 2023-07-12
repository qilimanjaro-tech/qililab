"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces.attenuator import Attenuator
from qililab.drivers.interfaces.awg import AWG
from qililab.drivers.interfaces.local_oscillator import LocalOscillator
from qililab.buses.interfaces import BusInterface
from qililab.pulse import PulseBusSchedule
from typing import Any

class DriveBus(BusInterface):
    """Qililab's driver for Drive Bus"""

    def __init__(self, qubit:int, awg: AWG, local_oscilator: LocalOscillator | None, attenuator: Attenuator | None, **kwargs):
        """Initialise the bus.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        super().__init__(**kwargs)
        self.qubit = qubit
        self.awg = awg
        self.local_oscillator = local_oscilator
        self.attenuator = attenuator

    def execute(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> None:
        """Execute a pulse bus schedule through an AWG Instrument belonging to the bus.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse Bus Schedule to generate QASM program.
            nshots (int): number of shots
            repetition_duration (int): repetition duration.
            num_bins (int): number of bins
        """
        self.awg.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, num_bins=num_bins)

    def set_parameter(self, param_name: str, value: Any) -> None:
        """Set parameter on the bus' instruments.

        Args:
            param (str): Parameter's name.
            value (float): Parameter's value
        """

    def get_parameter(self, param_name: str) -> Any:
        """Return value associated to a parameter on the bus' instrument.

        Args:
            param (str): Parameter's name.
        Returns:
            value (float): Parameter's value
        """
