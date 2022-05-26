"""BusTarget class."""
from abc import ABC, abstractmethod
from typing import List, Union

from qililab.settings import Settings
from qililab.typings import BusElement, BusElementName
from qililab.utils import nested_dataclass


class BusTarget(BusElement, ABC):
    """BusTarget class"""

    name: BusElementName

    @nested_dataclass
    class BusTargetSettings(Settings):
        """BusTargetSettings class."""

    settings: BusTargetSettings

    @property
    def id_(self):
        """BusTarget 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def category(self):
        """BusTarget 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    @abstractmethod
    def qubit_ids(self) -> List[int]:
        """BusTarget 'qubit_ids' property.

        Returns:
            List[int]: List containing the IDs of the qubits connected to the BusTarget.
        """

    @abstractmethod
    def get_qubit(self, id_: int) -> Union["BusTarget", None]:
        """Return specific Qubit class. Return None if qubit is not found.

        Args:
            id_ (int): ID of the qubit.

        Returns:
            (Qubit | None): Qubit class.
        """
