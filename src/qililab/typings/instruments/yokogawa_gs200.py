"""Class YokogawaGS200"""
from qcodes.instrument_drivers.yokogawa.GS200 import GS200 as Driver_GS200

from qililab.typings.instruments.device import Device


class YokogawaGS200(Driver_GS200, Device):
    """Typing class of the GS200 class defined by Qcodes."""
