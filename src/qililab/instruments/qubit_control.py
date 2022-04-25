"""QubitControl class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument


class QubitControl(Instrument):
    """Abstract base class defining all instruments used to control the qubits."""

    @dataclass
    class QubitControlSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific pulsar.

        Args:
            id (str): ID of the settings.
            name (str): Unique name of the settings.
            category (str): General name of the settings category. Options are "platform", "qubit_control",
            "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
            ip (str): IP address of the instrument.
        """

    settings: QubitControlSettings
