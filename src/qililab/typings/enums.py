"""Enum classes"""
from enum import Enum


class Category(Enum):
    """Category of settings.

    Args:
        enum (str): Available types of settings cattegories:
        * platform
        * qubit
        * qubit_instrument
        * signal_generator
        * buses
        * bus
        * mixer
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


class PulseShapeOptions(Enum):
    """Pulse shape options.

    Args:
        Enum (str): Available types of PulseShape options:
        * gaussian
    """

    GAUSSIAN = "gaussian"


class BusType(Enum):
    """Bus types.

    Args:
        enum (str): Available types of Bus:
        * control
        * readout
    """

    CONTROL = "control"
    READOUT = "readout"


class BusElementName(Enum):
    """Bus element names.

    Args:
        enum (str): Available bus element names:
        * mixer_up
        * mixer_down
        * qubit
        * qblox_qcm
        * qblox_qrm
        * rohde_schwarz
    """

    MIXER_UP = "mixer_up"
    MIXER_DOWN = "mixer_down"
    QUBIT = "qubit"
    RESONATOR = "resonator"
    QBLOX_QCM = "qblox_qcm"
    QBLOX_QRM = "qblox_qrm"
    ROHDE_SCHWARZ = "rohde_schwarz"
