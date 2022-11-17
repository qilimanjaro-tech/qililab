"""Enum classes"""
from enum import Enum


class Category(Enum):
    """Category of settings.

    Args:
        enum (str): Available types of settings categories:
        * platform
        * qubit
        * awg
        * signal_generator
        * buses
        * bus
        * schema
        * resonator
        * node
        * instrument_controller
    """

    PLATFORM = "platform"
    QUBIT = "qubit"
    AWG = "awg"
    SIGNAL_GENERATOR = "signal_generator"
    SCHEMA = "schema"
    RESONATOR = "resonator"
    BUSES = "buses"
    BUS = "bus"
    SYSTEM_CONTROL = "system_control"
    EXPERIMENT = "experiment"
    ATTENUATOR = "attenuator"
    DC_SOURCE = "dc_source"
    CHIP = "chip"
    NODE = "node"
    INSTRUMENT_CONTROLLER = "instrument_controller"


class Instrument(Enum):
    """Instrument.

    Args:
        enum (str): Available types of instruments:
        * platform
        * awg
        * signal_generator
        * system_control
        * attenuator
    """

    PLATFORM = "platform"
    AWG = "awg"
    SIGNAL_GENERATOR = "signal_generator"
    SYSTEM_CONTROL = "system_control"
    ATTENUATOR = "attenuator"


class InstrumentControllerSubCategory(Enum):
    """Instrument Controller subcategory types.

    Args:
        enum (str): Available types of instrument controllers:
        * single_instrument
        * multiple_instruments
    """

    SINGLE = "single_instrument"
    MULTI = "multiple_instruments"


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


class GateName(Enum):
    """Gate names.

    Args:
        enum (str): Available types of gate names:
        * I
        * X
        * Y
        * M
        * RX
        * RY
        * XY
    """

    I = "I"  # noqa: E741
    X = "X"
    RX = "RX"
    Y = "Y"
    RY = "RY"
    XY = "XY"
    M = "M"


class MasterGateSettingsName(Enum):
    """Master Gate Settings names.
    Args:
        enum (str): Available types of master gate settings names:
        * master_amplitude_gate
        * master_duration_gate
    """

    MASTER_AMPLITUDE_GATE = "master_amplitude_gate"
    MASTER_DURATION_GATE = "master_duration_gate"


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


class PulseName(Enum):
    """Pulse names.

    Args:
        Enum (str): Available types of Pulse names:
        * pulse
        * readout_pulse
    """

    PULSE = "pulse"
    READOUT_PULSE = "readout_pulse"


class PulseShapeName(Enum):
    """Pulse shape options.

    Args:
        Enum (str): Available types of PulseShape options:
        * gaussian
    """

    GAUSSIAN = "gaussian"
    DRAG = "drag"
    RECTANGULAR = "rectangular"


class PulseShapeSettingsName(Enum):
    """Pulse Shape Settings names.
    Args:
        enum (str): Available types of pulse shape settings names:
        * num_sigmas
        * drag_coefficient
    """

    NUM_SIGMAS = "num_sigmas"
    DRAG_COEFFICIENT = "drag_coefficient"


class BusSubcategory(Enum):
    """Bus types.

    Args:
        enum (str): Available types of Bus:
        * control
        * readout
    """

    CONTROL = "control"
    READOUT = "readout"


class SystemControlSubcategory(Enum):
    """Bus element names. Contains names of bus elements that are not instruments.

    Args:
        enum (str): Available bus element names:
        * mixer_based_system_control
        * simulated_system_control
    """

    MIXER_BASED_SYSTEM_CONTROL = "mixer_based_system_control"
    SIMULATED_SYSTEM_CONTROL = "simulated_system_control"


class NodeName(Enum):
    """Node names.

    Args:
        enum (str): Available node names:
        * qubit
        * resonator
        * coupler
    """

    QUBIT = "qubit"
    RESONATOR = "resonator"
    COUPLER = "coupler"
    PORT = "port"


class InstrumentName(Enum):
    """Instrument names.

    Args:
        enum (str): Available instrument element names:
        * QCM -> Exactly as Qblox InstrumentType
        * QRM -> Exactly as Qblox InstrumentType
        * rohde_schwarz
        * mini_circuits
        * mixer_based_system_control
        * integrated_system_control
        * simulated_system_control
        * keithley_2600
    """

    QBLOX_QCM = "QCM"
    QBLOX_QRM = "QRM"
    ROHDE_SCHWARZ = "rohde_schwarz"
    MIXER_BASED_SYSTEM_CONTROL = "mixer_based_system_control"
    INTEGRATED_SYSTEM_CONTROL = "integrated_system_control"
    SIMULATED_SYSTEM_CONTROL = "simulated_system_control"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator
    KEITHLEY2600 = "keithley_2600"


class InstrumentControllerName(Enum):
    """Instrument Controller names.

    Args:
        enum (str): Available instrument controller element names:
        * qblox_pulsar
        * qblox_cluster
        * rohde_schwarz
        * mini_circuits
        * keithley_2600
    """

    QBLOX_PULSAR = "qblox_pulsar"
    QBLOX_CLUSTER = "qblox_cluster"
    ROHDE_SCHWARZ = "rohde_schwarz"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator
    KEITHLEY2600 = "keithley_2600"


class Parameter(Enum):
    """Parameter names."""

    FREQUENCY = "frequency"
    GAIN = "gain"
    DURATION = "duration"
    AMPLITUDE = "amplitude"
    PHASE = "phase"
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
    SAMPLING_RATE = "sampling_rate"
    INTEGRATION = "integration"
    INTEGRATION_LENGTH = "integration_length"
    ACQUISITION_DELAY_TIME = "acquisition_delay_time"
    ATTENUATION = "attenuation"
    REPETITION_DURATION = "repetition_duration"
    HARDWARE_AVERAGE = "hardware_average"
    SOFTWARE_AVERAGE = "software_average"
    NUM_BINS = "num_bins"
    SEQUENCE_TIMEOUT = "sequence_timeout"
    MASTER_AMPLITUDE_GATE = "master_amplitude_gate"
    MASTER_DURATION_GATE = "master_duration_gate"
    EXTERNAL = "external"
    RESET = "reset"
    CURRENT = "current"
    VOLTAGE = "voltage"
    HARDWARE_MODULATION = "hardware_modulation"
    HARDWARE_DEMODULATION = "hardware_demodulation"
    HARDWARE_INTEGRATION = "hardware_integration"
    ACQUISITION_MODE = "acquisition_mode"
    FREQUENCIES = "frequencies"


class ResultName(Enum):
    """Result names.

    Args:
        enum (str): Available result element names:
        * qblox
        * simulator
    """

    QBLOX = "qblox"
    SIMULATOR = "simulator"


class ConnectionName(Enum):
    """Connection names.

    Args:
        enum (str): Available connection element names:
        * tcp_ip
        * usb
    """

    TCP_IP = "tcp_ip"
    USB = "usb"


class InstrumentTypeName(Enum):
    """Instrument Type names (the name of the class).

    Args:
        enum (str): Available instrument type element names:
        * QbloxQCM
        * QbloxQRM
        * SGS100A
        * Attenuator
        * Keithley2600
    """

    QBLOX_QCM = "QbloxQCM"
    QBLOX_QRM = "QbloxQRM"
    ROHDE_SCHWARZ = "SGS100A"
    MINI_CIRCUITS = "Attenuator"
    KEITHLEY2600 = "Keithley2600"


class LivePlotTypes(Enum):
    """Live Plot Types.

    Args:
        enum (str): Available plot element types:
        * LINES
        * SCATTER
        * HEATMAP
    """

    LINES = "LINES"
    SCATTER = "SCATTER"
    HEATMAP = "HEATMAP"
