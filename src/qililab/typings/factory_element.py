"""FactoryElement class"""
from qililab.typings.enums import (
    BusSubCategory,
    ConnectionName,
    InstrumentControllerName,
    InstrumentName,
    NodeName,
    PulseShapeName,
    ResultName,
    SystemControlSubCategory,
)


class FactoryElement:
    """Class FactoryElement"""

    name: (
        SystemControlSubCategory
        | PulseShapeName
        | ResultName
        | InstrumentName
        | NodeName
        | ConnectionName
        | InstrumentControllerName
        | BusSubCategory
    )
