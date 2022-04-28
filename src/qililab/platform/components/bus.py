from dataclasses import asdict, dataclass, field
from typing import List

from qililab.instruments import Mixer, QubitInstrument, SignalGenerator
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils import BusElementHashTable, dict_factory
from qililab.settings import Settings
from qililab.typings import Category, YAMLNames


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
            qubit_instrument (QubitInstrument): Class containing the instrument used for control/readout of the qubits.
            signal_generator (SignalGenerator): Class containing the signal generator instrument.
            mixer (Mixer): Class containing the mixer object, used for up- or down-conversion.
            resonator (Resonator): Class containing the resonator object.
        """

        elements: List[QubitInstrument | SignalGenerator | Mixer | Resonator]
        signal_generator: SignalGenerator = field(init=False)
        mixer: Mixer = field(init=False)
        resonator: Resonator = field(init=False)
        qubit_instrument: QubitInstrument = field(init=False)

        def __post_init__(self):
            """Cast each element to its corresponding class."""
            super().__post_init__()
            for idx, settings in enumerate(self.elements):
                self.elements[idx] = BusElementHashTable.get(settings[YAMLNames.NAME.value])(settings)
                setattr(self, settings["category"], BusElementHashTable.get(settings[YAMLNames.NAME.value])(settings))

        def get_element(self, category: Category, id_: int):
            """Get bus element. Return None if element is not found.

            Args:
                category (str): Category of element.
                id_ (int): ID of element.

            Returns:
                (QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator | None): Element class.
            """
            if category == Category.QUBIT:
                return self.resonator.get_qubit(id_=id_)
            return next(
                (element for element in self.elements if element.category == category and element.id_ == id_), None
            )

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

    def __init__(self, settings: dict | BusSettings):
        if isinstance(settings, dict):
            settings = self.BusSettings(**settings)
        self.settings = settings

    def connect(self):
        """Connect to the instruments."""
        self.qubit_instrument.connect()
        self.signal_generator.connect()

    def setup(self):
        """Setup instruments."""
        self.qubit_instrument.setup()
        self.signal_generator.setup()

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
    def qubit_instrument(self):
        """Bus 'qubit_instrument' property.

        Returns:
            QubitInstrument: settings.qubit_instrument.
        """
        return self.settings.qubit_instrument

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over bus elements."""
        return self.settings.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.settings.elements.__getitem__(key)
