"""Resonator class."""
from dataclasses import dataclass
from typing import List

from qililab.platform.components.targets.qubit import Qubit
from qililab.platform.components.targets.target import Target
from qililab.typings import BusElementName
from qililab.utils import Factory


@Factory.register
class Resonator(Target):
    """Resonator class"""

    name = BusElementName.RESONATOR

    @dataclass
    class ResonatorSettings(Target.BusTargetSettings):
        """Contains the settings obtained from calibrating the qubit.

        Args:
            qubits (List[Qubit]): List containing the class of the qubits connected to the resonator.
        """

        qubits: List[Qubit]

        def __post_init__(self):
            """Cast list of qubits settings to Qubit objects."""
            super().__post_init__()
            self.qubits = [Qubit(qubit_settings) for qubit_settings in self.qubits]

    settings: ResonatorSettings

    def __init__(self, settings: dict):
        self.settings = self.ResonatorSettings(**settings)

    @property
    def qubits(self):
        """Resonator 'qubits' property.

        Returns:
            List[Qubit]: settings.qubits.
        """
        return self.settings.qubits

    @property
    def qubit_ids(self):
        """Resonator 'qubit_ids' property.

        Returns:
            List[int]: List containing the IDs of the qubits connected to the resonator.
        """
        return [qubit.id_ for qubit in self.qubits]

    def get_qubit(self, id_: int) -> Qubit | None:
        """Return specific Qubit class. Return None if qubit is not found.

        Args:
            id_ (int): ID of the qubit.

        Returns:
            (Qubit | None): Qubit class.
        """
        return next((qubit for qubit in self.qubits if qubit.id_ == id_), None)
