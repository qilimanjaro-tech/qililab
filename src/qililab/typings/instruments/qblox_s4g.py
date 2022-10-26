"""Class Qblox S4g"""
from qblox_instruments.qcodes_drivers.spi_rack_modules import (
    S4gModule as Driver_S4gModule,
)

from qililab.typings.instruments.device import Device


class QbloxS4g(Driver_S4gModule, Device):
    """Typing class of the S4g class defined by Qblox."""
