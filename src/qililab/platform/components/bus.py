"""Bus class."""
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from qililab.instruments import Mixer, PulseSequence, QubitInstrument, SignalGenerator
from qililab.platform.components.qubit import Qubit
from qililab.platform.components.resonator import Resonator
from qililab.platform.utils import BusElementHashTable, dict_factory
from qililab.settings import Settings
from qililab.typings import Category, YAMLNames


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object, which
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
            resonator (Optional[Resonator]): Class containing the resonator object.
            qubit (Optional[Qubit]): Class containing the qubit object.
        """

        elements: List[QubitInstrument | SignalGenerator | Mixer | Qubit | Resonator]
        signal_generator: SignalGenerator = field(init=False)
        mixer_up: Mixer = field(init=False)
        mixer_down: Optional[Mixer] = field(init=False)
        qubit_instrument: QubitInstrument = field(init=False)
        resonator: Optional[Resonator] = field(init=False)
        qubit: Optional[Qubit] = field(init=False)

        def __post_init__(self):
            """Cast each element to its corresponding class."""
            super().__post_init__()
            for idx, settings in enumerate(self.elements):
                elem_obj = BusElementHashTable.get(settings[YAMLNames.NAME.value])(settings)
                self.elements[idx] = elem_obj
                attr_name = settings[YAMLNames.CATEGORY.value]
                if Category(attr_name) == Category.MIXER:
                    attr_name = settings[YAMLNames.NAME.value]
                setattr(self, attr_name, elem_obj)

    settings: BusSettings

    def connect(self):
        """Connect to the instruments."""
        self.qubit_instrument.connect()
        self.signal_generator.connect()

    def setup(self):
        """Setup instruments."""
        self.qubit_instrument.setup()
        self.signal_generator.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.qubit_instrument.start()
        self.signal_generator.start()

    def run(self, pulse_sequence: PulseSequence):
        """Run the given pulse sequence."""
        self.qubit_instrument.run(pulse_sequence=pulse_sequence)

    def close(self):
        """Close connection to the instruments."""
        self.qubit_instrument.close()
        self.signal_generator.close()

    def to_dict(self):
        """Return a dict representation of the BusSettings class"""
        return {
            "id_": self.id_,
            "name": self.name,
            "category": self.category.value,
            "elements": [asdict(element.settings, dict_factory=dict_factory) for element in self.elements],
        }

    def get_element(self, category: Category, id_: int):
        """Get bus element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator | None): Element class.
        """
        return next((element for element in self.elements if element.category == category and element.id_ == id_), None)

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
    def mixer_up(self):
        """Bus 'mixer' property.

        Returns:
            Mixer: settings.mixer.
        """
        return self.settings.mixer_up

    @property
    def qubit_instrument(self):
        """Bus 'qubit_instrument' property.

        Returns:
            QubitInstrument: settings.qubit_instrument.
        """
        return self.settings.qubit_instrument

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over elements."""
        return self.elements.__iter__()

    def __getitem__(self, key):
        """Redirect __get_item__ magic method."""
        return self.elements.__getitem__(key)
