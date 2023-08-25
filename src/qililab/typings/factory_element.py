"""FactoryElement class"""
from qililab.typings.enums import (
    BusDriverName,
    ConnectionName,
    InstrumentControllerName,
    InstrumentInterfaceName,
    InstrumentName,
    NodeName,
    PulseDistortionName,
    PulseShapeName,
    ResultName,
    SystemControlName,
)


class FactoryElement:  # pylint: disable=too-few-public-methods
    """Class FactoryElement"""

    name: (
        SystemControlName
        | PulseDistortionName
        | PulseShapeName
        | ResultName
        | InstrumentName
        | NodeName
        | ConnectionName
        | InstrumentControllerName
        | InstrumentInterfaceName
        | BusDriverName
    )
