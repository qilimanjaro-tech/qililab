from abc import ABC, abstractmethod

from qililab.config import logger, raise_error


class AbstractPlatform(ABC):
    """Abstract platform for controlling quantum devices."""

    def __init__(self, name: str) -> None:
        """
        Args:
            name (str): Name of the platform
        """
        logger.info(f"Loading platform {name}")
        self.name = name

    def __str__(self) -> str:
        """String representation of the platform

        Returns:
            str: Name of the platform
        """
        return self.name

    @abstractmethod
    def connect(self) -> None:
        """Connect to lab instruments using the specified calibration settings."""
        raise_error(NotImplementedError)

    @abstractmethod
    def setup(self) -> None:
        """Configure instruments using the specified calibration settings."""
        raise_error(NotImplementedError)

    @abstractmethod
    def start(self) -> None:
        """Turn on lab instruments."""
        raise_error(NotImplementedError)

    @abstractmethod
    def stop(self) -> None:
        """Turn off lab instruments."""
        raise_error(NotImplementedError)

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from lab instruments."""
        raise_error(NotImplementedError)

    # TODO: Replace 'object' with PulseSequence class (when defined)
    @abstractmethod
    def execute(self, sequence: object, nshots: int = None):
        """Execute a pulse sequence.

        Args:
            sequence (PulseSequence): Pulse sequence to execute.
            nshots (int): Number of shots to sample from the experiment. If ``None`` the default value provided as hardware_avg in the calibration json will be used.

        Returns:
            Readout results.
        """
        raise_error(NotImplementedError)
