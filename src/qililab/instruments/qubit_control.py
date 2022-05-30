"""QubitControl class."""
from qililab.instruments.awg import AWG
from qililab.utils import nested_dataclass


class QubitControl(AWG):
    """Abstract base class defining all instruments used to control the qubits."""

    @nested_dataclass
    class QubitControlSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitControlSettings
