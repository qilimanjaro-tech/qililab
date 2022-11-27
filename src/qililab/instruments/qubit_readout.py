"""QubitReadout class."""
from abc import abstractmethod
from dataclasses import dataclass

from qililab.instruments.awg import AWG
from qililab.result.result import Result


class AWGReadout(AWG):
    """Abstract base class defining all instruments used to readout the qubits."""

    @dataclass
    class AWGReadoutSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            delay_before_readout (int): Delay (ns) between the readout pulse and the acquisition.
        """

        acquisition_delay_time: int  # ns

    settings: AWGReadoutSettings

    @property
    def acquisition_delay_time(self):
        """AWG 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.acquisition_delay_time

    @abstractmethod
    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
