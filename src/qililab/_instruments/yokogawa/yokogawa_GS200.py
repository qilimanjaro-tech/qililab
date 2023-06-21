from typing import Any

from qcodes.instrument_drivers.yokogawa.GS200 import GS200 as QCodesYokogawaGS200

from qililab._instruments.interfaces import VoltageSource


class YokogawaGS200(QCodesYokogawaGS200, VoltageSource):
    """Qililab's driver for the YokogawaGS200 acting as VoltageSource

    Args:
        name (str): What this instrument is called locally.
        address (str): The GPIB or USB address of this instrument
        kwargs (Any | dict): kwargs to be passed to VisaInstrument class
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name=name, address=address, **kwargs)
