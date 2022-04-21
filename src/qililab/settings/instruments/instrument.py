from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class InstrumentSettings(Settings):
    """Contains the settings of an instrument.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
        ip (str): IP address of the instrument.
    """

    ip: str
