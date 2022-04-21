"""Enum classes"""
from enum import Enum
from typing import Dict, List, Tuple


class CategorySettings(Enum):
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
    QUBIT_CONTROL = "qubit_control"
    QUBIT_READOUT = "qubit_readout"
    SIGNAL_GENERATOR = "signal_generator"
    SCHEMA = "schema"
    RESONATOR = "resonator"
    BUSES = "buses"
    MIXER = "mixer"


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


def enum_dict_factory(data: List[Tuple[str, int | float | str | Enum]]):
    """Dict factory used in the asdict() dataclass function. Replace all Enum classes by its corresponding values."""
    result: Dict[str, int | float | str] = {}
    for key, value in data:
        if isinstance(value, Enum):
            value = str(value.value)
        result = result | {key: value}
    return result
