"""SignalGenerator class."""
from abc import abstractmethod
from typing import Any

from qililab.typings.factory_element import InstrumentFactoryElement


class BaseInstrument(InstrumentFactoryElement):
    """Base Interface for all instruments."""

    @property
    @abstractmethod
    def params(self):
        """parameters property."""

    @property
    @abstractmethod
    def alias(self):
        """alias property."""

    @abstractmethod
    def set(self, param_name: str, value: Any) -> None:
        """Set instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.
            value (Any): The new value to set.
        """

    @abstractmethod
    def get(self, param_name: str) -> Any:
        """Get instrument parameter.

        Args:
            param_name (str): The name of a parameter of this instrument.

        Returns:
            Any: Current value of the parameter.
        """
