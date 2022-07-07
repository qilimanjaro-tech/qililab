"""FactoryElement class"""
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentName,
    NodeName,
    PulseShapeName,
    ResultName,
    SystemControlSubcategory,
)


class FactoryElement:
    """Class FactoryElement"""

    name: SystemControlSubcategory | PulseShapeName | ResultName | InstrumentName | NodeName | ConnectionName | InstrumentControllerName
