"""YOkogawaGS200 driver."""
from qcodes.instrument_drivers.yokogawa.GS200 import GS200 as QCodesYokogawaGS200

from qililab.drivers.interfaces import CurrentSource, VoltageSource


class YokogawaGS200(QCodesYokogawaGS200, VoltageSource, CurrentSource):
    """
    Qililab's driver for the YokogawaGS200 acting as VoltageSource and CurrentSource

    Args:
        name (str): What this instrument is called locally.
        address (str): The GPIB or USB address of this instrument
        kwargs (Any | dict): kwargs to be passed to VisaInstrument class
    """
