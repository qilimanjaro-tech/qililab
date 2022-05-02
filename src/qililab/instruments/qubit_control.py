"""QubitControl class."""
from qililab.instruments.qubit_instrument import QubitInstrument
from qililab.utils import nested_dataclass


class QubitControl(QubitInstrument):
    """Abstract base class defining all instruments used to control the qubits."""

    @nested_dataclass
    class QubitControlSettings(QubitInstrument.QubitInstrumentSettings):
        """Contains the settings of a specific pulsar."""

    settings: QubitControlSettings
