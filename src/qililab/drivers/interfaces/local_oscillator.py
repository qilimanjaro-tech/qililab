from abc import ABC, abstractmethod
from typing import Any


class LocalOscillator(ABC):
    """Interface of a local oscillator."""
    @property
    @abstractmethod
    def parameters(self):
        """parameters property."""

    @abstractmethod
    def set(self, param_name: str, value: Any) -> None:
        """Set parameter from name

        Args:
            param_name (str): The name of a parameter of this instrument.
            value (Any): The new value to set.
        """

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Get parameter from name

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """

    @abstractmethod
    def on(self) -> None:
        """Start RF output"""

    @abstractmethod
    def off(self) -> None:
        """Stop RF outout"""
