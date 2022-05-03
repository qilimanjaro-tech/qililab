"""Enum classes"""
from enum import Enum


class Category(Enum):
    """Category of settings.

    Args:
        enum (str): Available types of settings cattegories:
        * platform
        * qubit
        * qblox_qcm
        * qblox_qrm
        * rohde_schwarz
        * schema
        * resonator
    """

    PLATFORM = "platform"
    QUBIT = "qubit"
    QUBIT_INSTRUMENT = "qubit_instrument"
    SIGNAL_GENERATOR = "signal_generator"
    SCHEMA = "schema"
    RESONATOR = "resonator"
    BUSES = "buses"
    MIXER = "mixer"
    BUS = "bus"


class ReferenceClock(Enum):
    """Qblox reference clock.

    Args:
        enum (str): Available types of reference clock:
        * Internal
        * External
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


class AcquireTriggerMode(Enum):
    """Qblox acquire trigger mode.

    Args:
        enum (str): Available types of trigger modes:
        * sequencer
        * level
    """

    SEQUENCER = "sequencer"
    LEVEL = "level"


class IntegrationMode(Enum):
    """Qblox integration mode.

    Args:
        enum (str): Available types of integration modes:
        * ssb
    """

    SSB = "ssb"


class SchemaDrawOptions(Enum):
    """Schema draw options.

    Args:
        enum (str): Available types of schema draw options:
        * print
        * file
    """

    PRINT = "print"
    FILE = "file"


class YAMLNames(Enum):
    """YAML names.

    Args:
        enum (str): Available types of YAML names:
        * platform
        * schema
        * id_
        * name
        * category
        * buses
        * pulse_sequence
        * execution
        * elements
        * readout
    """

    PLATFORM = "platform"
    SCHEMA = "schema"
    ID_ = "id_"
    NAME = "name"
    CATEGORY = "category"
    BUS = "bus"
    BUSES = "buses"
    PULSE_SEQUENCE = "pulse_sequence"
    EXECUTION = "execution"
    ELEMENTS = "elements"
    READOUT = "readout"


class PulseShapeOptions(Enum):
    """Pulse shape options.

    Args:
        Enum (str): Available types of PulseShape options:
        * gaussian
    """

    GAUSSIAN = "gaussian"
