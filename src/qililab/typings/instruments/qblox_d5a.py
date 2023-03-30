"""Class Qblox D5a"""
from qblox_instruments.qcodes_drivers.spi_rack_modules import D5aModule as Driver_D5aModule

from qililab.typings.instruments.device import Device


class QbloxD5a(Driver_D5aModule, Device):
    """Typing class of the D5a class defined by Qblox."""
