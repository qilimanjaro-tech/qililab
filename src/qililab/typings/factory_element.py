"""BusElement class"""
from qililab.typings.enums import BusElementName, PulseShapeName


class FactoryElement:
    """Class BusElement. All bus element classes must inherit from this class."""

    name: BusElementName | PulseShapeName
