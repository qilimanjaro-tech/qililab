"""QubitControl class."""
from dataclasses import dataclass

from qililab.instruments.awg import AWG


class QubitControl(AWG):
    """Abstract base class defining all instruments used to control the qubits."""

    @dataclass
    class QubitControlSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitControlSettings
