""" Module containing the interface for the voltage_sources """
from abc import ABC, abstractmethod
from typing import Any


class VoltageSource(ABC):
    """Voltage source interface with set, get, on & off abstract methods"""

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
        """Start VoltageSource output"""

    @abstractmethod
    def off(self) -> None:
        """Stop VoltageSource outout"""
