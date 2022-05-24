"""MixerBasedSystemControl class."""
from dataclasses import dataclass
from typing import Generator, Optional, Tuple

from qililab.constants import YAML
from qililab.instruments.mixer import Mixer, MixerDown, MixerUp
from qililab.instruments.qubit_instrument import QubitInstrument
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.typings import BusElementName, Category
from qililab.utils import Factory


@Factory.register
class MixerBasedSystemControl(SystemControl):
    """MixerBasedSystemControl class."""

    name = BusElementName.MIXER_BASED_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class MixerBasedSystemControlSettings(SystemControl.SystemControlSettings):
        """MixerBasedSystemControlSettings class."""

        mixer_up: MixerUp
        qubit_instrument: QubitInstrument
        signal_generator: SignalGenerator
        mixer_down: Optional[MixerDown] = None

        def __post_init__(self):
            """Cast each bus element to its corresponding class."""
            for name, value in self:
                if name == MixerUp.name.value:
                    setattr(self, name, MixerUp(value))
                elif name == MixerDown.name.value:
                    setattr(self, name, MixerDown(value))
                elif isinstance(value, dict):
                    elem_obj = Factory.get(value.pop(YAML.NAME))(value)
                    setattr(self, name, elem_obj)

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SignalGenerator | Mixer | QubitInstrument | dict], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if isinstance(value, SignalGenerator | Mixer | QubitInstrument | dict):
                    yield name, value

    settings: MixerBasedSystemControlSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.MixerBasedSystemControlSettings(**settings)

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
        self.signal_generator.start()

    def run(self, pulse_sequence: PulseSequence, nshots: int, loop_duration: int):
        """Run the given pulse sequence."""
        return self.qubit_instrument.run(pulse_sequence=pulse_sequence, nshots=nshots, loop_duration=loop_duration)

    def close(self):
        """Close connection to the instruments."""
        self.qubit_instrument.close()
        self.signal_generator.close()

    @property
    def frequency(self):
        """SystemControl 'frequency' property."""
        return self.qubit_instrument.frequency

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
    def qubit_instrument(self):
        """Bus 'qubit_instrument' property.
        Returns:
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.qubit_instrument

    def get_element(self, category: Category, id_: int):
        """Get system control element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (QubitInstrument | SignalGenerator | Mixer | None): Element class.
        """
        return next((element for _, element in self if element.category == category and element.id_ == id_), None)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()
