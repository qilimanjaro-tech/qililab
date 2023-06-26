"""YokogawaGS200 monitor & monitor drivers."""
from qcodes.instrument_drivers.yokogawa.GS200 import GS200_Monitor as QCodesYokogawaGS200Monitor
from qcodes.instrument_drivers.yokogawa.GS200 import GS200Program as QCodesYokogawaGS200Program


class YokogawaGS200Monitor(QCodesYokogawaGS200Monitor):
    """
    Monitor part of the GS200. This is only enabled if it is installed in the GS200 (it is an optional extra).

    The units will be automatically updated as required.

    To measure:
    `YokogawaGS200.measure.measure()`

    Args:
        parent (QCodes.GS200): Defaulted to the corresponding QCodes driver already, don't pass it
        name (str): instrument name
        present (Bool)
    """


class YokogawaGS200Program(QCodesYokogawaGS200Program):
    """
    Program part of the GS200.

    Args:
        parent (QCodes.GS200): Defaulted to the corresponding QCodes driver already, don't pass it
        name (str): instrument name
    """
