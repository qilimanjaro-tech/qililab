"""Enum classes"""
from enum import Enum


class Category(Enum):
    """Category of settings.

    Args:
        enum (str): Available types of settings cattegories:
        * platform
        * qubit
        * awg
        * signal_generator
        * buses
        * bus
        * mixer
        * schema
        * resonator
    """

    PLATFORM = "platform"
    QUBIT = "qubit"
    AWG = "awg"
    SIGNAL_GENERATOR = "signal_generator"
    SCHEMA = "schema"
    RESONATOR = "resonator"
    BUSES = "buses"
    MIXER = "mixer"
    BUS = "bus"
    SYSTEM_CONTROL = "system_control"
    EXPERIMENT = "experiment"
    STEP_ATTENUATOR = "step_attenuator"


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


class AcquisitionName(Enum):
    """Acquisition names.

    Args:
        enum (str): Available types of acquisition names:
        * single
    """

    SINGLE = "single"
    LARGE = "large"


class SchemaDrawOptions(Enum):
    """Schema draw options.

    Args:
        enum (str): Available types of schema draw options:
        * print
        * file
    """

    PRINT = "print"
    FILE = "file"


class PulseShapeName(Enum):
    """Pulse shape options.

    Args:
        Enum (str): Available types of PulseShape options:
        * gaussian
    """

    GAUSSIAN = "gaussian"
    DRAG = "drag"
    RECTANGULAR = "rectangular"


class BusSubcategory(Enum):
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
    MIXER_BASED_SYSTEM_CONTROL = "mixer_based_system_control"
    INTEGRATED_SYSTEM_CONTROL = "integrated_system_control"
    SIMULATED_SYSTEM_CONTROL = "simulated_system_control"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator


class Parameter(Enum):
    """Parameter names."""

    FREQUENCY = "frequency"
    GAIN = "gain"
    READOUT_DURATION = "readout_duration"
    READOUT_AMPLITUDE = "readout_amplitude"
    READOUT_PHASE = "readout_phase"
    DELAY_BETWEEN_PULSES = "delay_between_pulses"
    DELAY_BEFORE_READOUT = "delay_before_readout"
    GATE_DURATION = "gate_duration"
    NUM_SIGMAS = "num_sigmas"
    DRAG_COEFFICIENT = "drag_coefficient"
    REFERENCE_CLOCK = "reference_clock"
    SEQUENCER = "sequencer"
    SYNC_ENABLED = "sync_enabled"
    POWER = "power"
    EPSILON = "epsilon"
    DELTA = "delta"
    OFFSET_I = "offset_i"
    OFFSET_Q = "offset_q"
    START_INTEGRATE = "start_integrate"
    SAMPLING_RATE = "sampling_rate"
    INTEGRATION_LENGTH = "integration_length"
    DELAY_TIME = "delay_time"
    ATTENUATION = "attenuation"
    REPETITION_DURATION = "repetition_duration"
    HARDWARE_AVERAGE = "hardware_average"
    SOFTWARE_AVERAGE = "software_average"


class ResultName(Enum):
    """Result names.

    Args:
        enum (str): Available bus element names:
        * qblox
        * simulator
    """

    QBLOX = "qblox"
    SIMULATOR = "simulator"
