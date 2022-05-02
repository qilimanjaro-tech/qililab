"""BusControl class."""
from dataclasses import dataclass, field

from qililab.instruments import QubitControl
from qililab.platform.components.bus import Bus
from qililab.platform.components.qubit import Qubit
from qililab.utils import nested_dataclass


@dataclass
class BusControl(Bus):
    """BusControl class. This bus contains a qubit control and a signal generator, which are connected
    through a mixer for up-conversion, and a qubit at the end of the bus.

    Args:
        settings (BusControlSettings): Bus settings.
    """

    @nested_dataclass
    class BusControlSettings(Bus.BusSettings):
        """BusSettings class.
        Args:
            qubit_control (QubitControl): Class containing the instrument used for control of the qubits.
            qubit (Qubit): Class containing the qubit object.
        """

        qubit: Qubit = field(init=False)
        qubit_instrument: QubitControl = field(init=False)

    settings: BusControlSettings

    def __init__(self, settings: dict):
        self.settings = self.BusControlSettings(**settings)

    @property
    def qubit(self):
        """Bus 'qubit' property.

        Returns:
            Resonator: settings.qubit.
        """
        return self.settings.qubit
