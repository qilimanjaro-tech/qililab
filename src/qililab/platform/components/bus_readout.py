"""BusReadout class."""
from dataclasses import dataclass

from qililab.platform.components.bus import Bus
from qililab.platform.components.resonator import Resonator
from qililab.typings import BusType, Category


class BusReadout(Bus):
    """BusReadout class. This bus contains a system control and a resonator, which is connected to
    one or multiple qubits.

    Args:
        qubit_instrument (QubitReadout): Class containing the instrument used for readout of the qubits.
        mixer_down (Mixer): Class containing the mixer object, used for down-conversion.
        resonator (Resonator): Class containing the resonator object.
    """

    @dataclass
    class BusReadoutSettings(Bus.BusSettings):
        """BusReadout settings."""

        resonator: Resonator

    settings: BusReadoutSettings
    bus_type = BusType.READOUT

    def __init__(self, settings: dict):
        self.settings = self.BusReadoutSettings(**settings)

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
