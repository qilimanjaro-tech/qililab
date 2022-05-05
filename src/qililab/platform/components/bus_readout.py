"""BusReadout class."""
from dataclasses import dataclass

from qililab.instruments import MixerDown, QubitReadout
from qililab.platform.components.bus import Bus
from qililab.platform.components.resonator import Resonator
from qililab.typings import Category


@dataclass
class BusReadout(Bus):
    """BusReadout class. This bus contains a qubit readout and a signal generator, which are connected
    through a mixer for up-conversion. The bus also contains a resonator, which should be connected to one or multiple qubits.
    We finally have another mixer used for down-conversion.

    Args:
        qubit_instrument (QubitReadout): Class containing the instrument used for readout of the qubits.
        mixer_down (Mixer): Class containing the mixer object, used for down-conversion.
        resonator (Resonator): Class containing the resonator object.
    """

    mixer_down: MixerDown
    resonator: Resonator
    qubit_instrument: QubitReadout

    def get_element(self, category: Category, id_: int):
        """Get bus element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitReadout | SignalGenerator | Mixer | Resonator | Qubit | None): Element class.
        """
        if category == Category.QUBIT:
            return self.resonator.get_qubit(id_=id_)
        return super().get_element(category=category, id_=id_)

    @property
    def qubit_ids(self):
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.
        """
        return self.resonator.qubit_ids
