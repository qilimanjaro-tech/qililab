from dataclasses import asdict, dataclass, field
from typing import List

from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils.bus_element_hash_table import BusElementHashTable
from qililab.platform.utils.dict_factory import dict_factory
from qililab.settings.settings import Settings


@dataclass
class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end/beginning of the bus there should be a resonator object, which
    is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @dataclass
    class BusSettings(Settings):
        """BusSettings class.
        Args:
            qubit_control (None | QubitControl): Class containing the qubit control instrument.
            qubit_readout (None | QubitReadout): Class containing the qubit readout instrument.
            signal_generator (SignalGenerator): Class containing the signal generator instrument.
            mixer (Mixer): Class containing the mixer object, used for up- or down-conversion.
            resonator (Resonator): Class containing the resonator object.
        """

        elements: List[QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator]
        signal_generator: SignalGenerator = field(init=False)
        mixer: Mixer = field(init=False)
        resonator: Resonator = field(init=False)
        qubit_control: None | QubitControl = field(init=False, default=None)
        qubit_readout: None | QubitReadout = field(init=False, default=None)

        def __post_init__(self):
            """Cast each element to its corresponding class."""
            super().__post_init__()
            for idx, settings in enumerate(self.elements):
                self.elements[idx] = BusElementHashTable.get(settings["name"])(settings)
                setattr(self, settings["category"], BusElementHashTable.get(settings["name"])(settings))

        def __iter__(self):
            """Redirect __iter__ magic method to iterate over elements."""
            return self.elements.__iter__()

        def to_dict(self):
            """Return a dict representation of the BusSettings class"""
            return {
                "id_": self.id_,
                "name": self.name,
                "category": self.category.value,
                "elements": [asdict(element.settings, dict_factory=dict_factory) for element in self.elements],
            }

    settings: BusSettings

    @property
    def id_(self):
        """Bus 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Bus 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Bus 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def elements(self):
        """Bus 'elements' property.

        Returns:
            List[QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator]: settings.elements.
        """
        return self.settings.elements

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.

        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    @property
    def mixer(self):
        """Bus 'mixer' property.

        Returns:
            Mixer: settings.mixer.
        """
        return self.settings.mixer

    @property
    def resonator(self):
        """Bus 'resonator' property.

        Returns:
            Resonator: settings.resonator.
        """
        return self.settings.resonator

    @property
    def qubit_control(self):
        """Bus 'qubit_control' property.

        Returns:
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.qubit_control

    @property
    def qubit_readout(self):
        """Bus 'qubit_readout' property.

        Returns:
            (QubitReadout | None): settings.qubit_readout.
        """
        return self.settings.qubit_readout

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over bus elements."""
        return self.settings.__iter__()
