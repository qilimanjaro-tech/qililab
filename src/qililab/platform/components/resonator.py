from dataclasses import dataclass
from typing import List

from qililab.platform.components.qubit import Qubit
from qililab.settings.settings import Settings


class Resonator:
    """Resonator class"""

    @dataclass
    class ResonatorSettings(Settings):
        """Contains the settings obtained from calibrating the qubit.

        Args:
            qubits (List[int]): List containing the IDs of the qubits connected to the resonator.
        """

        qubits: List[Qubit]

        def __post_init__(self):
            """Cast list of qubits settings to Qubit objects."""
            self.qubits = [Qubit(qubit_settings) for qubit_settings in self.qubits]

    settings: ResonatorSettings

    def __init__(self, settings: dict):
        self.settings = self.ResonatorSettings(**settings)

    @property
    def id_(self):
        """Resonator 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Resonator 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Resonator 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def qubits(self):
        """Resonator 'qubits' property.

        Returns:
            List[Qubit]: settings.qubits.
        """
        return self.settings.qubits
