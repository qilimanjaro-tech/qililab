"""Constants"""
from typing import TypeAlias

from qblox_instruments import Pulsar
from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A

DEFAULT_PLATFORM_FILENAME = "platform"
DEFAULT_SETTINGS_FOLDERNAME = "qili"
INSTRUMENT_TYPES: TypeAlias = Pulsar | RohdeSchwarz_SGS100A  # Types of all instruments used in qililab
