from abc import abstractmethod

from .base_instrument import BaseInstrument

class LocalOscillator(BaseInstrument):
    """Interface of a local oscillator."""
    @abstractmethod
    def on(self) -> None:
        """Start RF output"""

    @abstractmethod
    def off(self) -> None:
        """Stop RF outout"""
