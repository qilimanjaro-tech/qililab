"""QubitReadout class."""
from qililab.instruments.awg import AWG
from qililab.utils import nested_dataclass


class QubitReadout(AWG):
    """Abstract base class defining all instruments used to readout the qubits."""

    @nested_dataclass
    class QubitReadoutSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            delay_before_readout (int): Delay (ns) between the readout pulse and the acquisition.
        """

        delay_time: int  # ns

    settings: QubitReadoutSettings

    @property
    def delay_time(self):
        """QbloxPulsar 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.delay_time
