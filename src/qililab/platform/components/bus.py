"""Bus class."""
from dataclasses import dataclass
from types import NoneType
from typing import Generator, Optional, Tuple

from qililab.constants import YAML
from qililab.instruments import (
    Mixer,
    MixerDown,
    MixerUp,
    QubitInstrument,
    SignalGenerator,
)
from qililab.platform.components.qubit import Qubit
from qililab.platform.components.resonator import Resonator
from qililab.pulse import PulseSequence
from qililab.settings import Settings
from qililab.typings import Category
from qililab.utils import BusElementFactory


class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end of the bus there should be a qubit or a resonator object,
    which is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    @dataclass(kw_only=True)
    class BusSettings(Settings):
        """Bus settings.

        Args:
            qubit_instrument (QubitInstrument): Class containing the instrument used for control/readout of the qubits.
            signal_generator (SignalGenerator): Class containing the signal generator instrument.
            mixer_up (Mixer): Class containing the mixer object used for up-conversion.
            mixer_down (Optional[Mixer]): Class containing the mixer object used for down-conversion.
            resonator (Optional[Resonator]): Class containing the resonator object.
            qubit (Optional[Qubit]): Class containing the qubit object.
        """

        signal_generator: SignalGenerator
        mixer_up: MixerUp
        qubit_instrument: QubitInstrument
        mixer_down: Optional[MixerDown] = None
        qubit: Optional[Qubit] = None
        resonator: Optional[Resonator] = None

        def __post_init__(self):
            """Cast each bus element to its corresponding class."""
            for name, value in self:
                if name == MixerUp.name.value:
                    setattr(self, name, MixerUp(value))
                elif name == MixerDown.name.value:
                    setattr(self, name, MixerDown(value))
                elif isinstance(value, dict):
                    elem_obj = BusElementFactory.get(value.pop(YAML.NAME))(value)
                    setattr(self, name, elem_obj)

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SignalGenerator | Mixer | Resonator | QubitInstrument | Qubit | dict], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if isinstance(value, SignalGenerator | Mixer | QubitInstrument | Qubit | Resonator | dict):
                    yield name, value

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
        return self.qubit_instrument.run(pulse_sequence=pulse_sequence)

    def close(self):
        """Close connection to the instruments."""
        self.qubit_instrument.close()
        self.signal_generator.close()

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.
        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    @property
    def mixer_up(self):
        """Bus 'mixer_up' property.
        Returns:
            Mixer: settings.mixer_up.
        """
        return self.settings.mixer_up

    @property
    def mixer_down(self):
        """Bus 'mixer_down' property.
        Returns:
            Mixer: settings.mixer_down.
        """
        return self.settings.mixer_down

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
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.qubit_instrument

    @property
    def qubit(self):
        """Bus 'qubit' property.

        Returns:
            Qubit: settings.qubit.
        """
        return self.settings.qubit

    @property
    def qubit_ids(self) -> list:
        """Bus 'qubit_ids' property.

        Returns:
            List[int]: IDs of the qubit connected to the bus.~
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

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()
