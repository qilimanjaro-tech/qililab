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


class Instrument(Enum):
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


class BusCategory(Enum):
    """Bus categories.

    Args:
        enum (str): Available categories of Bus:
        * time_domain
        * continuous
        * simulated
    """

    TIME_DOMAIN = "time_domain"
    CONTINUOUS = "continuous"
    SIMULATED = "simulated"


class BusSubCategory(Enum):
    """Bus subcategories.

    Args:
        enum (str): Available subcategories of Bus:
        * baseband
        * control
        * time_domain_readout
        * current_bias
        * microwave_bias
        * continuous_readout
        * simulated
    """

    BASEBAND = "baseband"
    CONTROL = "control"
    TIME_DOMAIN_READOUT = "readout"
    CURRENT_BIAS = "current_bias"
    MICROWAVE_BIAS = "microwave_bias"
    CONTINUOUS_READOUT = "readout"
    SIMULATED = "simulated"


class SystemControlCategory(Enum):
    """SystemControl categories.

    Args:
        enum (str): Available categories of SystemControl:
        * time_domain
        * continuous
        * simulated
    """

    TIME_DOMAIN = "time_domain"
    CONTINUOUS = "continuous"
    SIMULATED = "simulated"


class SystemControlSubCategory(Enum):
    """SystemControl subcategories.

    Args:
        enum (str): Available subcategories of SystemControl:
        * baseband
        * control
        * time_domain_readout
        * current_bias
        * microwave_bias
        * continuous_readout
        * simulated
    """

    BASEBAND = "baseband"
    CONTROL = "control"
    TIME_DOMAIN_READOUT = "readout"
    CURRENT_BIAS = "current_bias"
    MICROWAVE_BIAS = "microwave_bias"
    CONTINUOUS_READOUT = "readout"
    SIMULATED = "simulated"


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
    COIL = "coil"
    PORT = "port"


class InstrumentName(Enum):
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


class InstrumentControllerName(Enum):
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


class SystemControlName(Enum):
    """System Control names.

    Args:
        enum (str): Available system control element names:
        * time_domain_baseband_system_control
        * time_domain_control_system_control
        * time_domain_readout_system_control
        * continuous_current_bias_system_control
        * continuous_microwave_bias_system_control
        * continuous_readout_system_control
    """

    TIME_DOMAIN_BASEBAND_SYSTEM_CONTROL = "time_domain_baseband_system_control"
    TIME_DOMAIN_CONTROL_SYSTEM_CONTROL = "time_domain_control_system_control"
    TIME_DOMAIN_READOUT_SYSTEM_CONTROL = "time_domain_readout_system_control"
    CONTINUOUS_CURRENT_BIAS_SYSTEM_CONTROL = "continuous_current_bias_system_control"
    CONTINUOUS_MICROWAVE_BIAS_SYSTEM_CONTROL = "continuous_microwave_bias_system_control"
    CONTINUOUS_READOUT_SYSTEM_CONTROL = "continuous_readout_system_control"
    SIMULATED_SYSTEM_CONTROL = "simulated_system_control"


class BusName(Enum):
    """System Control names.

    Args:
        enum (str): Available bus element names:
        * time_domain_baseband_bus
        * time_domain_control_bus
        * time_domain_readout_bus
        * continuous_current_bias_bus
        * continuous_microwave_bias_bus
        * continuous_readout_bus
    """

    TIME_DOMAIN_BASEBAND_BUS = "time_domain_baseband_bus"
    TIME_DOMAIN_CONTROL_BUS = "time_domain_control_bus"
    TIME_DOMAIN_READOUT_BUS = "time_domain_readout_bus"
    CONTINUOUS_CURRENT_BIAS_BUS = "continuous_current_bias_bus"
    CONTINUOUS_MICROWAVE_BIAS_BUS = "continuous_microwave_bias_bus"
    CONTINUOUS_READOUT_BUS = "continuous_readout_bus"
    SIMULATED_BUS = "simulated_bus"


class Parameter(Enum):
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
    GAIN_PATH0 = "gain_path0"
    GAIN_PATH1 = "gain_path1"
    OFFSET_PATH0 = "offset_path0"
    OFFSET_PATH1 = "offset_path1"


class ResultName(Enum):
    """Result names.

    Args:
        enum (str): Available result element names:
        * qblox
        * simulator
    """

    QBLOX = "qblox"
    SIMULATOR = "simulator"
    VECTOR_NETWORK_ANALYZER = "vector_network_analyzer"


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


class VNATriggerModes(Enum):
    """Vector Network Analyzers Trigger Modes

    Args:
        enum (str): Available types of trigger modes:
        * INT
        * BUS
    """

    INT = "INT"
    BUS = "BUS"


class VNAScatteringParameters(Enum):
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


class Node(Enum):
    """Node elements

    Args:
        enum (str): Available elements of chip node:
        * nodes
        * frequency
    """

    NODES = "nodes"
    FREQUENCY = "frequency"
    QUBIT_INDEX = "qubit_index"


class CallbackOrder(Enum):
    """Callback order of method

    Args:
        enum (str): Order of calling method with respect to set_paramter method:
        * after
        * before
    """

    AFTER_SET_PARAMETER = "after_set_parameter"
    BEFORE_SET_PARAMETER = "before_set_parameter"
