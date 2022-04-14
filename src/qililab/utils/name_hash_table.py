"""Class used as hashtable to load the class corresponding to a given category"""
from qililab.instruments import SGS100A, QbloxPulsarQCM, QbloxPulsarQRM
from qililab.platforms import Platform
from qililab.qubit import Qubit
from qililab.resonator import Resonator


class NameHashTable:
    """Hash table that maps strings to classes"""

    platform = Platform
    qblox_qrm = QbloxPulsarQRM
    qblox_qcm = QbloxPulsarQCM
    rohde_schwarz = SGS100A
    resonator = Resonator
    qubit = Qubit
