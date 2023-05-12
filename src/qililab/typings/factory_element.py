"""FactoryElement class"""
from qililab.typings.enums import (
    ConnectionName,
    InstrumentControllerName,
    InstrumentName,
    NodeName,
    PulseDistortionName,
    PulseShapeName,
    ResultName,
    SystemControlName,
)


class FactoryElement:
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
    )
