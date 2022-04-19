"""Class used as hashtable to load the class corresponding to a given category"""
from typing import Type

from qililab.instruments import SGS100A, QbloxPulsarQCM, QbloxPulsarQRM
from qililab.platforms import Platform
from qililab.qubit import Qubit
from qililab.resonator import Resonator


class NameHashTable:
    """Hash table that loads a specific class given an object's name."""

    platform = Platform
    qblox_qrm = QbloxPulsarQRM
    qblox_qcm = QbloxPulsarQCM
    rohde_schwarz = SGS100A
    resonator = Resonator
    qubit = Qubit

    @classmethod
    def get(cls, name: str) -> Type[Platform | QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit]:
        """Return class attribute."""
        return getattr(cls, name)
