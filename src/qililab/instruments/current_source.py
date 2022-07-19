"""CurrentSource class."""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.constants import CURRENTSOURCE
from qililab.instruments.instrument import Instrument


class CurrentSource(Instrument):
    """Abstract base class defining all instruments used to generate currents."""

    @dataclass
    class CurrentSourceSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            current (float): Current of the instrument in A.
                Value range is (-8, 8).
        """

        current: float

    settings: CurrentSourceSettings

    @property
    def current(self):
        """CurrentSource 'current' property.

        Returns:
            float: settings.current.
        """
        return self.settings.current

    @abstractmethod
    def start(self):
        """Turn instrument on."""

    def to_dict(self):
        """Return a dict representation of the CurrentSource class."""
        return {key: value for key, value in super().to_dict().items() if key != CURRENTSOURCE.CURRENT}
        # TODO: Ask why except CURRENT? (was frequency in signal generator)
