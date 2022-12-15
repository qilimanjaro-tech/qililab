"""FactoryElement class"""
from qililab.typings.enums import (
    BusName,
    ConnectionName,
    InstrumentControllerName,
    InstrumentName,
    NodeName,
    PulseShapeName,
    ResultName,
    SystemControlName,
)


class FactoryElement:
    """Class FactoryElement"""

    name: (
        SystemControlName
        | PulseShapeName
        | ResultName
        | InstrumentName
        | NodeName
        | ConnectionName
        | InstrumentControllerName
        | BusName
    )
