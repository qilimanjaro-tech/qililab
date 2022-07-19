"""Class SPI Rack"""
import qblox_instruments

from qililab.typings.instruments.device import Device


class SPI_Rack(qblox_instruments.SpiRack, Device):
    """Typing class of the SPI Rack class defined by Qblox."""
