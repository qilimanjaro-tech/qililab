"""BusReadout class."""
from dataclasses import dataclass, field

from qililab.instruments import Mixer, QubitReadout
from qililab.platform.components.bus import Bus
from qililab.platform.components.resonator import Resonator
from qililab.typings import Category
from qililab.utils import nested_dataclass


@dataclass
class BusReadout(Bus):
    """BusReadout class. This bus contains a qubit readout and a signal generator, which are connected
    through a mixer for up-conversion. The bus also contains a resonator, which should be connected to one or multiple qubits.
    We finally have another mixer used for down-conversion.

    Args:
        settings (BusReadoutSettings): Bus settings.
    """

    @nested_dataclass
    class BusReadoutSettings(Bus.BusSettings):
        """BusSettings class.
        Args:
            qubit_readout (QubitReadout): Class containing the instrument used for readout of the qubits.
            signal_generator (SignalGenerator): Class containing the signal generator instrument.
            mixer_up (Mixer): Class containing the mixer object, used for up-conversion.
            mixer_down (Mixer): Class containing the mixer object, used for down-conversion.
            resonator (Resonator): Class containing the resonator object.
        """

        mixer_down: Mixer = field(init=False)
        resonator: Resonator = field(init=False)
        qubit_instrument: QubitReadout = field(init=False)

    settings: BusReadoutSettings

    def __init__(self, settings: dict):
        self.settings = self.BusReadoutSettings(**settings)

    @property
    def mixer_down(self):
        """Bus 'mixer' property.

        Returns:
            Mixer: settings.mixer.
        """
        return self.settings.mixer_down

    @property
    def resonator(self):
        """Bus 'resonator' property.

        Returns:
            Resonator: settings.resonator.
        """
        return self.settings.resonator

    def get_element(self, category: Category, id_: int):
        """Get bus element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitReadout | SignalGenerator | Mixer | Resonator | Qubit | None): Element class.
        """
        if category == Category.QUBIT:
            return self.resonator.get_qubit(id_=id_)  # pylint: disable=no-member
        return super().get_element(category=category, id_=id_)
