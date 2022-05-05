"""BusControl class."""
from dataclasses import dataclass

from qililab.instruments import QubitControl
from qililab.platform.components.bus import Bus
from qililab.platform.components.qubit import Qubit


@dataclass
class BusControl(Bus):
    """BusControl class. This bus contains a qubit control and a signal generator, which are connected
    through a mixer for up-conversion, and a qubit at the end of the bus.

    Args:
        qubit_instrument (QubitControl): Class containing the instrument used for control of the qubits.
        qubit (Qubit): Class containing the qubit object.
    """

    qubit: Qubit
    qubit_instrument: QubitControl

    @property
    def qubit_ids(self):
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.
        """
        return [self.qubit.id_]
