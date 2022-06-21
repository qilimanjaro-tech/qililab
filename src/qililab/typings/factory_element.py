"""BusElement class"""
from qililab.typings.enums import (
    BusElementName,
    InstrumentName,
    PulseShapeName,
    ResultName,
)


class FactoryElement:
    """Class BusElement. All bus element classes must inherit from this class."""

    name: BusElementName | PulseShapeName | ResultName | InstrumentName
