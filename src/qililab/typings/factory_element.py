"""FactoryElement class"""
from qililab.typings.enums import (
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
    )
