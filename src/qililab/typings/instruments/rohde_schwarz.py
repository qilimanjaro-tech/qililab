"""Class Rohde Schwarz SGS100A"""
from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A

from qililab.typings.instruments.device import Device


class RohdeSchwarzSGS100A(RohdeSchwarz_SGS100A, Device):
    """Typing class of the QCoDeS driver for the Rohde & Schwarz SGS100A signal generator."""
