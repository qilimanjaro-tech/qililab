from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class InstrumentSettings(Settings):
    """Contains the settings of an instrument.

    Args:
        name (str): Name of the settings.
        category (str): Name of the category. Options are "platform", "instrument", "qubit" and "resonator".
        ip (str): IP address of the instrument.
    """

    ip: str
