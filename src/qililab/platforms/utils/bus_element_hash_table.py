"""Class used as hashtable to load the class corresponding to a given category"""
from typing import Type

from qililab.instruments import SGS100A, Mixer, QbloxPulsarQCM, QbloxPulsarQRM
from qililab.platforms.components.qubit import Qubit
from qililab.platforms.components.resonator import Resonator


class BusElementHashTable:
    """Hash table that loads a specific class given an object's name."""

    qblox_qrm = QbloxPulsarQRM
    qblox_qcm = QbloxPulsarQCM
    rohde_schwarz = SGS100A
    resonator = Resonator
    qubit = Qubit
    mixer = Mixer

    @classmethod
    def get(cls, name: str) -> Type[QbloxPulsarQRM | QbloxPulsarQCM | SGS100A | Resonator | Qubit | Mixer]:
        """Return class attribute."""
        return getattr(cls, name)
