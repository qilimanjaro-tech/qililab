"""BusElement class"""
from qililab.typings.enums import (
    InstrumentName,
    NodeName,
    PulseShapeName,
    ResultName,
    SystemControlSubcategory,
)


class FactoryElement:
    """Class BusElement. All bus element classes must inherit from this class."""

    name: SystemControlSubcategory | PulseShapeName | ResultName | InstrumentName | NodeName
