"""PulsedGates class. Contains the gates that can be directly translated into a pulse."""
from abc import ABC, abstractmethod
from typing import List, Tuple, Type

from qibo.abstractions.gates import Gate


class PulsedGate(ABC):
    """Settings of a specific pulsed gate."""

    class_type: Type[Gate]
    amplitude: float
    phase: float

    @classmethod
    @abstractmethod
    def translate(cls, parameters: None | float | List[float]) -> Tuple[float, float]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
