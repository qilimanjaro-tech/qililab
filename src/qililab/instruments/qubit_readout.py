"""QubitReadout class."""
from qililab.instruments.qubit_instrument import QubitInstrument
from qililab.utils import nested_dataclass


class QubitReadout(QubitInstrument):
    """Abstract base class defining all instruments used to readout the qubits."""

    @nested_dataclass
    class QubitReadoutSettings(QubitInstrument.QubitInstrumentSettings):
        """Contains the settings of a specific pulsar.

        Args:
            delay_before_readout (int): Delay (ns) between the readout pulse and the acquisition.
        """

        delay_before_readout: int  # ns

    settings: QubitReadoutSettings

    @property
    def delay_before_readout(self):
        """QbloxPulsar 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.delay_before_readout
