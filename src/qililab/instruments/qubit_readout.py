"""QubitReadout class."""
from dataclasses import dataclass

from qililab.instruments.qubit_instrument import QubitInstrument


class QubitReadout(QubitInstrument):
    """Abstract base class defining all instruments used to readout the qubits."""

    @dataclass
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
