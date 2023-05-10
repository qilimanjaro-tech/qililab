"""Enum classes"""
from enum import Enum


class Category(str, Enum):
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
        * voltage_source
        * current_source
        * digital_analog_converter
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
    VNA = "vna"
    CHIP = "chip"
    NODE = "node"
    INSTRUMENT_CONTROLLER = "instrument_controller"
    VOLTAGE_SOURCE = "voltage_source"
    CURRENT_SOURCE = "current_source"
    ADC = "adc"


class Instrument(str, Enum):
    """Instrument.

    Args:
        enum (str): Available types of instruments:
        * platform
        * awg
        * signal_generator
        * attenuator
        * voltage_source
        * current_source
    """

    PLATFORM = "platform"
    AWG = "awg"
    SIGNAL_GENERATOR = "signal_generator"
    ATTENUATOR = "attenuator"
    VOLTAGE_SOURCE = "voltage_source"
    CURRENT_SOURCE = "current_source"


class InstrumentControllerSubCategory(str, Enum):
    """Instrument Controller subcategory types.

    Args:
        enum (str): Available types of instrument controllers:
        * single_instrument
        * multiple_instruments
    """

    SINGLE = "single_instrument"
    MULTI = "multiple_instruments"


class ReferenceClock(str, Enum):
    """Qblox reference clock.

    Args:
        enum (str): Available types of reference clock:
        * Internal
        * External
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


class AcquireTriggerMode(str, Enum):
    """Qblox acquire trigger mode.

    Args:
        enum (str): Available types of trigger modes:
        * sequencer
        * level
    """

    SEQUENCER = "sequencer"
    LEVEL = "level"


class IntegrationMode(str, Enum):
    """Qblox integration mode.

    Args:
        enum (str): Available types of integration modes:
        * ssb
    """

    SSB = "ssb"


class GateName(str, Enum):
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


class MasterGateSettingsName(str, Enum):
    """Master Gate Settings names.
    Args:
        enum (str): Available types of master gate settings names:
        * master_amplitude_gate
        * master_duration_gate
    """

    MASTER_AMPLITUDE_GATE = "master_amplitude_gate"
    MASTER_DURATION_GATE = "master_duration_gate"


class AcquisitionName(str, Enum):
    """Acquisition names.

    Args:
        enum (str): Available types of acquisition names:
        * single
    """

    SINGLE = "single"
    LARGE = "large"


class SchemaDrawOptions(str, Enum):
    """Schema draw options.

    Args:
        enum (str): Available types of schema draw options:
        * print
        * file
    """

    PRINT = "print"
    FILE = "file"


class PulseShapeName(str, Enum):
    """Pulse shape options.

    Args:
        Enum (str): Available types of PulseShape options:
        * gaussian
    """

    GAUSSIAN = "gaussian"
    DRAG = "drag"
    RECTANGULAR = "rectangular"


class PulseShapeSettingsName(str, Enum):
    """Pulse Shape Settings names.
    Args:
        enum (str): Available types of pulse shape settings names:
        * num_sigmas
        * drag_coefficient
    """

    NUM_SIGMAS = "num_sigmas"
    DRAG_COEFFICIENT = "drag_coefficient"


class NodeName(str, Enum):
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
    COIL = "coil"
    PORT = "port"


class InstrumentName(str, Enum):
    """Instrument names.

    Args:
        enum (str): Available instrument element names:
        * QCM -> Exactly as Qblox InstrumentType
        * QRM -> Exactly as Qblox InstrumentType
        * rohde_schwarz
        * mini_circuits
        * keithley_2600
        * qblox_D5a
        * qblox_S4g
        * keysight_e5080b
        * agilent_e5071B
    """

    QBLOX_QCM = "QCM"
    QBLOX_QRM = "QRM"
    ROHDE_SCHWARZ = "rohde_schwarz"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator
    KEITHLEY2600 = "keithley_2600"
    QBLOX_D5A = "D5a"
    QBLOX_S4G = "S4g"
    KEYSIGHT_E5080B = "keysight_e5080b"
    AGILENT_E5071B = "agilent_e5071B"


class InstrumentControllerName(str, Enum):
    """Instrument Controller names.

    Args:
        enum (str): Available instrument controller element names:
        * qblox_pulsar
        * qblox_cluster
        * rohde_schwarz
        * mini_circuits
        * keithley_2600
        * keysight_e5080b
        * agilent_e5071B
    """

    QBLOX_PULSAR = "qblox_pulsar"
    QBLOX_CLUSTER = "qblox_cluster"
    ROHDE_SCHWARZ = "rohde_schwarz"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator
    KEITHLEY2600 = "keithley_2600"
    QBLOX_SPIRACK = "qblox_spi_rack"
    KEYSIGHT_E5080B = "keysight_e5080b_controller"
    AGILENT_E5071B = "agilent_e5071B_controller"


class SystemControlName(str, Enum):
    """System Control names.

    Args:
        enum (str): Available system control element names:
        * system_control
        * readout_system_control
        * simulated_system_control
    """

    SYSTEM_CONTROL = "system_control"
    READOUT_SYSTEM_CONTROL = "readout_system_control"
    SIMULATED_SYSTEM_CONTROL = "simulated_system_control"


class Parameter(str, Enum):
    """Parameter names."""

    BUS_FREQUENCY = "bus_frequency"
    LO_FREQUENCY = "frequency"
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
    GAIN_IMBALANCE = "gain_imbalance"
    PHASE_IMBALANCE = "phase_imbalance"
    SAMPLING_RATE = "sampling_rate"
    INTEGRATION = "integration"
    INTEGRATION_LENGTH = "integration_length"
    ACQUISITION_DELAY_TIME = "acquisition_delay_time"
    ATTENUATION = "attenuation"
    REPETITION_DURATION = "repetition_duration"
    SOFTWARE_AVERAGE = "software_average"
    NUM_BINS = "num_bins"
    SEQUENCE_TIMEOUT = "sequence_timeout"
    MASTER_AMPLITUDE_GATE = "master_amplitude_gate"
    MASTER_DURATION_GATE = "master_duration_gate"
    EXTERNAL = "external"
    RESET = "reset"
    HARDWARE_MODULATION = "hardware_modulation"
    HARDWARE_DEMODULATION = "hardware_demodulation"
    HARDWARE_INTEGRATION = "hardware_integration"
    SCOPE_ACQUIRE_TRIGGER_MODE = "scope_acquire_trigger_mode"
    SCOPE_HARDWARE_AVERAGING = "scope_hardware_averaging"
    IF = "intermediate_frequency"
    VOLTAGE = "voltage"
    CURRENT = "current"
    RAMPING_ENABLED = "ramping_enabled"
    RAMPING_RATE = "ramp_rate"
    SPAN = "span"
    SCATTERING_PARAMETER = "scattering_parameter"
    FREQUENCY_SPAN = "frequency_span"
    FREQUENCY_CENTER = "frequency_center"
    FREQUENCY_START = "frequency_start"
    FREQUENCY_STOP = "frequency_stop"
    IF_BANDWIDTH = "if_bandwidth"
    AVERAGING_ENABLED = "averaging_enabled"
    NUMBER_AVERAGES = "number_averages"
    TRIGGER_MODE = "trigger_mode"
    NUMBER_POINTS = "number_points"
    NUM_SEQUENCERS = "num_sequencers"
    INTEGRATION_MODE = "integration_mode"
    ACQUISITION_TIMEOUT = "acquisition_timeout"
    MAX_CURRENT = "max_current"
    MAX_VOLTAGE = "max_voltage"
    SCOPE_STORE_ENABLED = "scope_store_enabled"
    GAIN_I = "gain_i"
    GAIN_Q = "gain_q"
    OFFSET_I = "offset_i"
    OFFSET_Q = "offset_q"
    OFFSET_OUT0 = "offset_out0"
    OFFSET_OUT1 = "offset_out1"
    OFFSET_OUT2 = "offset_out2"
    OFFSET_OUT3 = "offset_out3"
    RF_ON = "rf_on"
    OPERATION_PARAMETER = "operation_parameter"
    DEVICE_TIMEOUT = "device_timeout"
    SWEEP_MODE = "sweep_mode"
    ELECTRICAL_DELAY = "electrical_delay"
    TIMEOUT = "timeout"
    NUM_FLIPS = "num_flips"
    WEIGHTS_I = "weights_i"
    WEIGHTS_Q = "weights_q"
    WEIGHED_ACQ_ENABLED = "weighed_acq_enabled"
    THRESHOLD = "threshold"


class ResultName(str, Enum):
    """Result names.

    Args:
        enum (str): Available result element names:
        * qblox
        * simulator
    """

    QBLOX = "qblox"
    SIMULATOR = "simulator"
    VECTOR_NETWORK_ANALYZER = "vector_network_analyzer"


class ConnectionName(str, Enum):
    """Connection names.

    Args:
        enum (str): Available connection element names:
        * tcp_ip
        * usb
    """

    TCP_IP = "tcp_ip"
    USB = "usb"


class InstrumentTypeName(str, Enum):
    """Instrument Type names (the name of the class).

    Args:
        enum (str): Available instrument type element names:
        * QbloxQCM
        * QbloxQRM
        * SGS100A
        * Attenuator
        * Keithley2600
        * QbloxD5a
        * QbloxS4g
    """

    QBLOX_QCM = "QbloxQCM"
    QBLOX_QRM = "QbloxQRM"
    ROHDE_SCHWARZ = "SGS100A"
    MINI_CIRCUITS = "Attenuator"
    KEITHLEY2600 = "Keithley2600"
    QBLOX_D5A = "QbloxD5a"
    QBLOX_S4G = "QbloxS4g"


class LivePlotTypes(str, Enum):
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


class VNATriggerModes(str, Enum):
    """Vector Network Analyzers Trigger Modes

    Args:
        enum (str): Available types of trigger modes:
        * INT
        * BUS
    """

    INT = "INT"
    BUS = "BUS"


class VNAScatteringParameters(str, Enum):
    """Vector Network Analyzers Scattering Parameters

    Args:
        enum (str): Available types of scattering parameters:
        * S11
        * S12
        * S22
        * S21
    """

    S11 = "S11"
    S12 = "S12"
    S22 = "S22"
    S21 = "S21"


class VNASweepModes(str, Enum):
    """Vector Network Analyzers Sweep Modes

    Args:
        enum (str): Available types of sweeping modes:
        * hold
        * cont
        * single
        * group
    """

    HOLD = "hold"
    CONT = "cont"
    SING = "single"
    GRO = "group"


class Node(str, Enum):
    """Node elements

    Args:
        enum (str): Available elements of chip node:
        * nodes
        * frequency
    """

    NODES = "nodes"
    FREQUENCY = "frequency"
    QUBIT_INDEX = "qubit_index"


class Qubits(str, Enum):
    ANY = "any"
    ONE = "one"
    TWO = "two"


class OperationName(str, Enum):
    """Operation names.

    Args:
        enum (str): Available types of operation names:
        * RXY
        * R180
        * X
        * WAIT
        * RESET
        * MEASURE
        * BARRIER
    """

    RXY = "Rxy"  # noqa: E741
    R180 = "R180"
    X = "X"
    CPHASE = "CPhase"
    WAIT = "Wait"
    RESET = "Reset"
    MEASURE = "Measure"
    BARRIER = "Barrier"
    PARKING = "Parking"
    PULSE = "Pulse"
    GAUSSIAN = "Gaussian"
    DRAG = "DRAG"
    SQUARE = "Square"


class OperationTimingsCalculationMethod(str, Enum):
    AS_SOON_AS_POSSIBLE = "as_soon_as_possible"
    AS_LATE_AS_POSSIBLE = "as_late_as_possible"


class ResetMethod(str, Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
