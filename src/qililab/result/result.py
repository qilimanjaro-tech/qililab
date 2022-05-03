"""Result class."""
from abc import ABC, abstractmethod


class Result(ABC):
    """Result class."""

    @abstractmethod
    def plot(self):
        """Plot results."""
