"""MixerBasedSystemControl class."""
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Generator, Tuple

from qililab.constants import YAML
from qililab.instruments.awg import AWG
from qililab.instruments.instruments import Instruments
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.instruments.utils import InstrumentFactory
from qililab.platform.components.bus_element import dict_factory
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

        awg: AWG
        signal_generator: SignalGenerator

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SignalGenerator | AWG | dict], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if isinstance(value, SignalGenerator | AWG | dict):
                    yield name, value

    settings: MixerBasedSystemControlSettings

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

    def connect(self):
        """Connect to the instruments."""
        self.awg.connect()
        self.signal_generator.connect()

    def setup(self):
        """Setup instruments."""
        self.awg.setup()
        self.signal_generator.setup()

    def start(self):
        """Start/Turn on the instruments."""
        self.signal_generator.start_sequencer()

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run the given pulse sequence."""
        return self.awg.run(
            pulse_sequence=pulse_sequence, nshots=nshots, repetition_duration=repetition_duration, path=path
        )

    def close(self):
        """Close connection to the instruments."""
        self.awg.close()
        self.signal_generator.close()

    def stop(self):
        """Stop instrument."""

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""

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
            (AWG | SignalGenerator | None): Element class.
        """
        return next((element for _, element in self if element.category == category and element.id_ == id_), None)

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {
            YAML.ID: self.id_,
            YAML.CATEGORY: self.settings.category.value,
            YAML.SUBCATEGORY: self.settings.subcategory.value,
        } | {
            key: {YAML.NAME: value.name.value} | asdict(value.settings, dict_factory=dict_factory)
            for key, value in self
            if not isinstance(value, dict)
        }

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in self.settings:
            if isinstance(value, dict):
                instrument_object = instruments.get(settings=value)
                setattr(self.settings, name, instrument_object)
