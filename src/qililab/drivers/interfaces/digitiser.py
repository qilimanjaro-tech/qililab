"""Generic interface for a Digitiser."""
from abc import abstractmethod
from typing import Any

from .base_instrument import BaseInstrument


class Digitiser(BaseInstrument):
    """Digitiser interface."""
    @abstractmethod
    def get_results(self) -> Any:
        """Get the acquisition results."""
