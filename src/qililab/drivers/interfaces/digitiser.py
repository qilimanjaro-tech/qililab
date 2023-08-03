"""Generic interface for a Digitiser."""
from abc import ABC, abstractmethod
from typing import Any


class Digitiser(ABC):
    """Digitiser interface."""

    @property
    @abstractmethod
    def params(self):
        """parameters property."""

    @abstractmethod
    def set(self, param_name: str, value: Any) -> None:
        """Set given `param_name` to the given `value`.

        Args:
            param_name (str): The name of a parameter of this instrument.
            value (Any): The new value to set.
        """

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Get parameter with name `param_name`.

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """

    @abstractmethod
    def get_results(self) -> Any:
        """Get the acquisition results."""
