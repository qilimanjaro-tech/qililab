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


from enum import Enum

from qililab.yaml import yaml


@yaml.register_class
class Parameter(str, Enum):
    """Parameter names."""

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
