"""BusControl class."""
from qililab.instruments import QubitControl
from qililab.platform.components.bus import Bus
from qililab.platform.components.qubit import Qubit
from qililab.utils import nested_dataclass


@nested_dataclass
class BusControl(Bus):
    """BusControl class. This bus contains a qubit control and a signal generator, which are connected
    through a mixer for up-conversion, and a qubit at the end of the bus.

    Args:
        qubit_instrument (QubitControl): Class containing the instrument used for control of the qubits.
        qubit (Qubit): Class containing the qubit object.
    """

    qubit: Qubit
    qubit_instrument: QubitControl
