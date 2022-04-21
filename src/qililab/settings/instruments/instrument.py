from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class InstrumentSettings(Settings):
    """Contains the settings of an instrument.

    Args:
        ip (str): IP address of the instrument.
    """

    ip: str
