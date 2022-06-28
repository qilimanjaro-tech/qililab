"""QubitReadout class."""
from dataclasses import dataclass

from qililab.instruments.awg import AWG


class QubitReadout(AWG):
    """Abstract base class defining all instruments used to readout the qubits."""

    @dataclass
    class QubitReadoutSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            delay_before_readout (int): Delay (ns) between the readout pulse and the acquisition.
        """

        acquisition_delay_time: int  # ns

    settings: QubitReadoutSettings

    @property
    def acquisition_delay_time(self):
        """QbloxPulsar 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.acquisition_delay_time
