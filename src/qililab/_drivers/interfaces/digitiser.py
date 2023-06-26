"""Generic interface `Digitiser` for instruments"""
from abc import ABC, abstractmethod
from typing import Any


class Digitiser(ABC):
    """Interface for all `Digitisers`"""

    @abstractmethod
    def set(self, param_name: str, value: Any) -> None:
        """Set parameter from name

        Args:
            param_name (str): The name of a parameter of this instrument.
            value (Any): The new value to set.
        """
        pass

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Get parameter from name

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """

        pass

    @abstractmethod
    def get_results(self) -> Any:
        """Return the results from the ``Digitiser``"""
        pass
