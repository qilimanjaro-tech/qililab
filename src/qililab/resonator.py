from typing import List

from qililab.qubit import Qubit
from qililab.settings import ResonatorSettings


class Resonator:
    """Resonator class"""

    qubits: List[Qubit]

    def __init__(self, settings: dict):
        self.settings = ResonatorSettings(**settings)
