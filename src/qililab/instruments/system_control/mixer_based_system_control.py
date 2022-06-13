"""MixerBasedSystemControl class."""
from pathlib import Path
from typing import Generator, Optional, Tuple

from qililab.constants import YAML
from qililab.instruments.awg import AWG
from qililab.instruments.mixer import Mixer, MixerDown, MixerUp
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.typings import BusElementName, Category
from qililab.utils import Factory, nested_dataclass


@Factory.register
class MixerBasedSystemControl(SystemControl):
    """MixerBasedSystemControl class."""

    name = BusElementName.MIXER_BASED_SYSTEM_CONTROL

    @nested_dataclass(kw_only=True)
    class MixerBasedSystemControlSettings(SystemControl.SystemControlSettings):
        """MixerBasedSystemControlSettings class."""

        mixer_up: MixerUp
        awg: AWG
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
        ) -> Generator[Tuple[str, SignalGenerator | Mixer | AWG | dict], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if isinstance(value, SignalGenerator | Mixer | AWG | dict):
                    yield name, value

    settings: MixerBasedSystemControlSettings

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = self.MixerBasedSystemControlSettings(**settings)

    def connect(self):
        """Connect to the instruments."""
        self.awg.connect()
        self.signal_generator.connect()

    def setup(self):
        """Setup instruments."""
        self.awg.setup_mixer_settings(mixer=self.mixer_up)
        self.awg.setup()
        self.signal_generator.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.signal_generator.start()

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run the given pulse sequence."""
        return self.awg.run(
            pulse_sequence=pulse_sequence, nshots=nshots, repetition_duration=repetition_duration, path=path
        )

    def close(self):
        """Close connection to the instruments."""
        self.awg.close()
        self.signal_generator.close()

    @property
    def frequency(self):
        """SystemControl 'frequency' property."""
        return self.awg.frequency

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
    def awg(self):
        """Bus 'awg' property.
        Returns:
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.awg

    @property
    def delay_time(self) -> int | None:
        """SystemControl 'delay_time' property.  Delay (in ns) between the readout pulse and the acquisition."""
        return self.awg.delay_time if isinstance(self.awg, QubitReadout) else None

    def get_element(self, category: Category, id_: int):
        """Get system control element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            (AWG | SignalGenerator | Mixer | None): Element class.
        """
        return next((element for _, element in self if element.category == category and element.id_ == id_), None)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()
