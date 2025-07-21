# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Enum classes"""

from enum import Enum

from qililab.yaml import yaml


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
        * Drag
        * CZ
        * Park
    """

    I = "I"
    X = "X"
    RX = "RX"
    Y = "Y"
    RY = "RY"
    XY = "XY"
    M = "M"
    Drag = "Drag"
    CZ = "CZ"
    Park = "Park"


class AcquisitionName(str, Enum):
    """Acquisition names.

    Args:
        enum (str): Available types of acquisition names:
        * single
    """

    SINGLE = "single"
    LARGE = "large"


class PulseDistortionName(str, Enum):
    """Pulse distortion options.

    Args:
        Enum (str): Available types of PulseDistortion options:
        * gaussian
    """

    BIAS_TEE_CORRECTION = "bias_tee"
    EXPONENTIAL_CORRECTION = "exponential"
    LFILTER = "lfilter"


class PulseShapeName(str, Enum):
    """Pulse shape options.

    Args:
        Enum (str): Available types of PulseShape options:
        * gaussian
    """

    GAUSSIAN = "gaussian"
    DRAG = "drag"
    RECTANGULAR = "rectangular"
    SNZ = "snz"
    COSINE = "cosine"
    FLATTOP = "flat_top"
    TWOSTEP = "two_step"


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
        * yokogawa_gs200
        * OPX -> Exactly as Quantum Machines InstrumentType
    """

    QBLOX_QCM = "QCM"
    QBLOX_QRM = "QRM"
    QRMRF = "QRM-RF"
    ROHDE_SCHWARZ = "rohde_schwarz"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator
    KEITHLEY2600 = "keithley_2600"
    QBLOX_D5A = "D5a"
    QBLOX_S4G = "S4g"
    KEYSIGHT_E5080B = "keysight_e5080b"
    YOKOGAWA_GS200 = "yokogawa_gs200"
    QCMRF = "QCM-RF"
    QUANTUM_MACHINES_CLUSTER = "quantum_machines_cluster"
    QDEVIL_QDAC2 = "qdevil_qdac2"


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


class VNATriggerType(str, Enum):
    """Vector Network Analyzers Trigger Type
    Args:
        enum (str): Available types of triggering types:
        * EDGE
        * LEV
    """

    EDGE = "EDGE"
    LEV = "LEV"


class VNATriggerSlope(str, Enum):
    """Vector Network Analyzers Trigger Slope
    Args:
        enum (str): Available types of triggering slopes:
        * POS
        * NEG
    """

    POS = "POS"
    NEG = "NEG"


class VNAFormatBorder(str, Enum):
    """Vector Network Analyzers Format Border
    Args:
        enum (str): Available types of trigger modes:
        * NORMal
        * SWAPped
    """

    NORM = "NORM"
    SWAP = "SWAP"


class VNASweepTypes(str, Enum):
    """Vector Network Analyzers Sweep Types
    Args:
        enum (str): Available types of sweeping types:
        * lin
        * log
        * pow
        * cw
        * segm
    """

    LIN = "LIN"
    LOG = "LOG"
    POW = "POW"
    CW = "CW"
    SEGM = "SEGM"


class VNASweepModes(str, Enum):
    """Vector Network Analyzers Sweep Types
    Args:
        enum (str): Available types of sweeping types:
        * hold
        * cont
        * single
        * group
    """

    HOLD = "HOLD"
    CONT = "CONT"
    SING = "SING"
    GRO = "GRO"


class VNATriggerSource(str, Enum):
    """Vector Network Analyzers Trigger Source
    Args:
        enum (str): Available types of trigger sources:
        * external
        * immediate
        * manual
    """

    EXT = "EXT"
    IMM = "IMM"
    MAN = "MAN"


class VNAAverageModes(str, Enum):
    """Vector Network Analyzers Average Modes
    Args:
        enum (str): Available types of average modes:
        * point
        * sweep
    """

    POIN = "POIN"
    SWE = "SWE"


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
        * yokogawa
        * qmm
    """

    QBLOX_CLUSTER = "qblox_cluster"
    ROHDE_SCHWARZ = "rohde_schwarz"
    MINI_CIRCUITS = "mini_circuits"  # step attenuator
    KEITHLEY2600 = "keithley_2600"
    QBLOX_SPIRACK = "qblox_spi_rack"
    KEYSIGHT_E5080B = "keysight_e5080b"
    YOKOGAWA_GS200 = "yokogawa_gs200_controller"
    QUANTUM_MACHINES_CLUSTER = "quantum_machines_cluster_controller"
    QDEVIL_QDAC2 = "qdevil_qdac2"


@yaml.register_class
class Parameter(str, Enum):
    """Parameter names."""
    OPERATION_MODE = "operation_mode"
    ALC = "alc"
    IQ_WIDEBAND = "iq_wideband"
    IQ_MODULATION = "iq_modulation"
    BUS_FREQUENCY = "bus_frequency"
    LO_FREQUENCY = "frequency"
    GAIN = "gain"
    DURATION = "duration"
    AMPLITUDE = "amplitude"
    PHASE = "phase"
    WAIT_TIME = "wait_time"
    DELAY_BETWEEN_PULSES = "delay_between_pulses"
    DELAY_BEFORE_READOUT = "delay_before_readout"
    GATE_DURATION = "gate_duration"
    GATE_PARAMETER = "gate_parameter"
    NUM_SIGMAS = "num_sigmas"
    DRAG_COEFFICIENT = "drag_coefficient"
    REFERENCE_CLOCK = "reference_clock"
    SEQUENCER = "sequencer"
    POWER = "power"
    GAIN_IMBALANCE = "gain_imbalance"
    PHASE_IMBALANCE = "phase_imbalance"
    SAMPLING_RATE = "sampling_rate"
    INTEGRATION = "integration"
    INTEGRATION_LENGTH = "integration_length"
    ATTENUATION = "attenuation"
    REPETITION_DURATION = "repetition_duration"
    SOFTWARE_AVERAGE = "software_average"
    SEQUENCE_TIMEOUT = "sequence_timeout"
    EXTERNAL = "external"
    RESET = "reset"
    HARDWARE_MODULATION = "hardware_modulation"
    HARDWARE_DEMODULATION = "hardware_demodulation"
    HARDWARE_INTEGRATION = "hardware_integration"
    SCOPE_ACQUIRE_TRIGGER_MODE = "scope_acquire_trigger_mode"
    SCOPE_HARDWARE_AVERAGING = "scope_hardware_averaging"
    IF = "intermediate_frequency"
    SOURCE_MODE = "source_mode"
    VOLTAGE = "voltage"
    CURRENT = "current"
    RAMPING_ENABLED = "ramping_enabled"
    RAMPING_RATE = "ramp_rate"
    SPAN = "span"
    LOW_PASS_FILTER = "low_pass_filter"  # noqa: S105
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
    INTEGRATION_MODE = "integration_mode"
    ACQUISITION_TIMEOUT = "acquisition_timeout"
    MAX_CURRENT = "max_current"
    MAX_VOLTAGE = "max_voltage"
    SCOPE_STORE_ENABLED = "scope_store_enabled"
    TIME_OF_FLIGHT = "time_of_flight"
    SMEARING = "smearing"
    GAIN_I = "gain_i"
    GAIN_Q = "gain_q"
    OFFSET_I = "offset_i"
    OFFSET_Q = "offset_q"
    DC_OFFSET = "dc_offset"
    OFFSET_OUT0 = "offset_out0"
    OFFSET_OUT1 = "offset_out1"
    OFFSET_OUT2 = "offset_out2"
    OFFSET_OUT3 = "offset_out3"
    RF_ON = "rf_on"
    OPERATION_PARAMETER = "operation_parameter"
    DEVICE_TIMEOUT = "device_timeout"
    SWEEP_TYPE = "sweep_type"
    ELECTRICAL_DELAY = "electrical_delay"
    TIMEOUT = "timeout"
    NUM_FLIPS = "num_flips"
    OUTPUT_STATUS = "output_status"
    WEIGHTS_I = "weights_i"
    WEIGHTS_Q = "weights_q"
    WEIGHED_ACQ_ENABLED = "weighed_acq_enabled"
    THRESHOLD = "threshold"
    THRESHOLD_ROTATION = "threshold_rotation"
    OUT0_LO_FREQ = "out0_lo_freq"
    OUT0_IN0_LO_FREQ = "out0_in0_lo_freq"
    OUT1_LO_FREQ = "out1_lo_freq"
    OUT0_LO_EN = "out0_lo_en"
    OUT0_IN0_LO_EN = "out0_in0_lo_en"
    OUT0_IN0_LO_FREQ_CAL_TYPE_DEFAULT = "out0_in0_lo_freq_cal_type_default"
    OUT0_LO_FREQ_CAL_TYPE_DEFAULT = "out0_lo_freq_cal_type_default"
    OUT1_LO_FREQ_CAL_TYPE_DEFAULT = "out1_lo_freq_cal_type_default"
    OUT1_LO_EN = "out1_lo_en"
    OUT0_ATT = "out0_att"
    IN0_ATT = "in0_att"
    OUT1_ATT = "out1_att"
    OUT0_OFFSET_PATH0 = "out0_offset_path0"
    OUT1_OFFSET_PATH0 = "out1_offset_path0"
    OUT0_OFFSET_PATH1 = "out0_offset_path1"
    OUT1_OFFSET_PATH1 = "out1_offset_path1"
    DELAY = "delay"
    B = "b"
    T_PHI = "t_phi"
    GATE_OPTIONS = "options"
    STEP_AUTO = "step_auto"
    STEP_SIZE = "step_size"
    CW_FREQUENCY = "cw_frequency"
    AVERAGES_MODE = "averages_mode"
    SWEEP_MODE = "sweep_mode"
    SWEEP_TIME = "sweep_time"
    SWEEP_TIME_AUTO = "sweep_time_auto"
    CLEAR_AVERAGES = "clear_averages"
    FORMAT_DATA = "format_data"
    SOURCE_POWER = "source_power"
    AVERAGES_ENABLED = "averages_enabled"
    FLUX = "flux"
    FORMAT_BORDER = "format_border"
    OPERATION_STATUS = "operation_status"
    TRIGGER_SOURCE = "trigger_source"
    TRIGGER_SLOPE = "trigger_slope"
    TRIGGER_TYPE = "trigger_type"
    SWEEP_GROUP_COUNT = "sweep_group_count"

    @classmethod
    def to_yaml(cls, representer, node):
        """Method to be called automatically during YAML serialization."""
        return representer.represent_scalar("!Parameter", f"{node.name}-{node.value}")

    @classmethod
    def from_yaml(cls, _, node):
        """Method to be called automatically during YAML deserialization."""
        _, value = node.value.split("-")
        return cls(value)


class ResultName(str, Enum):
    """Result names.

    Args:
        enum (str): Available result element names:
        * qblox
    """

    QBLOX = "qblox"
    QBLOX_QPROGRAM_MEASUREMENT = "qblox_qprogram_measurement"
    VECTOR_NETWORK_ANALYZER = "vector_network_analyzer"
    QUANTUM_MACHINES = "quantum_machines"
    QUANTUM_MACHINES_MEASUREMENT = "quantum_machines_measurement"


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
        * YokogawaGS200
        * QDevilQDac2
    """

    QBLOX_QCM = "QbloxQCM"
    QBLOX_QRM = "QbloxQRM"
    ROHDE_SCHWARZ = "SGS100A"
    MINI_CIRCUITS = "Attenuator"
    KEITHLEY2600 = "Keithley2600"
    QBLOX_D5A = "QbloxD5a"
    QBLOX_S4G = "QbloxS4g"
    YOKOGAWA_GS200 = "YokogawaGS200"
    QDEVIL_QDAC2 = "QDevilQDac2"
    KEYSIGHT_E5080B = "E5080B"


class ResetMethod(str, Enum):
    PASSIVE = "passive"
    ACTIVE = "active"


class SourceMode(str, Enum):
    """Source Modes"""

    CURRENT = "current"
    VOLTAGE = "voltage"


class Line(str, Enum):
    """Chip line"""

    FLUX = "flux"
    DRIVE = "drive"
    READOUT = "readout"
