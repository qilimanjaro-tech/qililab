"""Bus class."""
from dataclasses import dataclass
from types import NoneType
from typing import Generator, Tuple

from qililab.constants import YAML
from qililab.instruments import MixerUp, QubitInstrument, SignalGenerator
from qililab.platform.components.qubit import Qubit
from qililab.platform.components.resonator import Resonator
from qililab.pulse import PulseSequence
from qililab.typings import Category
from qililab.utils import BusElementFactory


@dataclass
class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        readout (bool): readout flag.
        qubit_instrument (QubitInstrument): Class containing the instrument used for control/readout of the qubits.
        signal_generator (SignalGenerator): Class containing the signal generator instrument.
        mixer_up (Mixer): Class containing the mixer object used for up-conversion.
        mixer_down (Optional[Mixer]): Class containing the mixer object used for down-conversion.
        resonator (Optional[Resonator]): Class containing the resonator object.
        qubit (Optional[Qubit]): Class containing the qubit object.
    """

    readout: bool
    signal_generator: SignalGenerator
    mixer_up: MixerUp
    qubit_instrument: QubitInstrument

    def __post_init__(self):
        """Cast each bus element to its corresponding class."""
        for name, value in self:
            if isinstance(value, dict):
                elem_obj = BusElementFactory.get(value.pop(YAML.NAME))(value)
                setattr(self, name, elem_obj)

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
        return self.qubit_instrument.run(pulse_sequence=pulse_sequence)

    def close(self):
        """Close connection to the instruments."""
        self.qubit_instrument.close()
        self.signal_generator.close()

    @property
    def qubit_ids(self) -> list:
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.
        """
        # FIXME: Cannot use ABC with dataclass
        raise NotImplementedError

    def get_element(self, category: Category, id_: int):
        """Get bus element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator | None): Element class.
        """
        return next((element for _, element in self if element.category == category and element.id_ == id_), None)

    def __iter__(
        self,
    ) -> Generator[Tuple[str, SignalGenerator | MixerUp | Resonator | QubitInstrument | Qubit], None, None]:
        """Iterate over Bus elements.

        Yields:
            Tuple[str, ]: _description_
        """
        for name, value in self.__dict__.items():
            if not isinstance(value, (NoneType, bool)):
                yield name, value
