"""Class EraSynthPlusPlus"""
from qcodes_contrib_drivers.drivers.ERAInstruments.erasynth import (
    ERASynthPlusPlus as QCoDeSEraSynthPlusPlus,
)

from qililab.typings.instruments.device import Device


class EraSynthPlusPlus(QCoDeSEraSynthPlusPlus, Device):
    """Typing class of the QCoDeS driver for the EraSynthPlusPlus signal generator."""
