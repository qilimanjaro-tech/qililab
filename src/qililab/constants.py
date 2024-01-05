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

"""Constants"""
# pylint: disable=too-few-public-methods

# Environment variables
DATA = "DATA"  # variable containing the path where data is saved
RUNCARDS = "RUNCARDS"  # variable containing the runcard's path

RESULTS_FILENAME = "results.yml"
EXPERIMENT_FILENAME = "experiment.yml"

DEFAULT_PLATFORM_NAME = "galadriel"
GALADRIEL_DEVICE_ID = 9

DEFAULT_TIMEOUT = 10 * 1000  # 10 seconds

GATE_ALIAS_REGEX = r"(?P<gate>[a-zA-Z]+)\((?P<qubits>\d+(?:,\s*\d+)*)\)"

# TODO: Distribute constants over different classes


class RUNCARD:
    """YAML constants."""

    NAME = "name"
    DEVICE_ID = "device_id"
    ALIAS = "alias"
    INSTRUMENT = "instrument"
    INSTRUMENTS = "instruments"
    ELEMENTS = "elements"
    READOUT = "readout"
    GATES_SETTINGS = "gates_settings"
    PLATFORM = "platform"
    BUSES = "buses"
    CHIP = "chip"
    AWG = "awg"
    SIGNAL_GENERATOR = "signal_generator"
    ATTENUATOR = "attenuator"
    SYSTEM_CONTROL = "system_control"
    INSTRUMENT_CONTROLLER = "instrument_controller"
    INSTRUMENT_CONTROLLERS = "instrument_controllers"
    FIRMWARE = "firmware"
    GATES = "gates"
    VOLTAGE_SOURCE = "voltage_source"
    CURRENT_SOURCE = "current_source"
    DISTORTIONS = "distortions"
    DELAY = "delay"


class PLATFORM:
    """Platform attribute names."""

    DELAY_BETWEEN_PULSES = "delay_between_pulses"
    DELAY_BEFORE_READOUT = "delay_before_readout"
    TIMINGS_CALCULATION_METHOD = "timings_calculation_method"
    RESET_METHOD = "reset_method"
    PASSIVE_RESET_DURATION = "passive_reset_duration"
    DEVICE_ID = "device_id"
    MINIMUM_CLOCK_TIME = "minimum_clock_time"


class CURRENTSOURCE:
    """CurrentSource attribute names."""

    CURRENT = "current"
    SPAN = "span"
    RAMPING_ENABLED = "ramping_enabled"
    RAMP_RATE = "ramp_rate"


class VOLTAGESOURCE:
    """VoltageSource attribute names."""

    VOLTAGE = "voltage"
    SPAN = "span"
    RAMPING_ENABLED = "ramping_enabled"
    RAMP_RATE = "ramp_rate"


class SIGNALGENERATOR:
    """SignalGenerator attribute names."""

    FREQUENCY = "frequency"
    PULSES = "pulses"


class EXPERIMENT:
    """Experiment constants."""

    HARDWARE_AVERAGE = "hardware_average"
    SOFTWARE_AVERAGE = "software_average"
    REPETITION_DURATION = "repetition_duration"
    SHAPE = "shape"
    RESULTS = "results"
    NUM_SCHEDULES = "num_schedules"
    LOOPS = "loops"
    OPTIONS = "options"
    DEVICE_ID = "device_id"
    REMOTE_DEVICE_MANUAL_OVERRIDE = "remote_device_manual_override"
    CONNECTION = "connection"
    CIRCUITS = "circuits"
    PULSE_SCHEDULES = "pulse_schedules"
    REMOTE_SAVE = "remote_save"
    DESCRIPTION = "description"


class BUS:
    """Bus constants."""

    PORT = "port"
    SYSTEM_CONTROL = "system_control"
    ATTENUATOR = "attenuator"
    SCHEDULES = "schedules"
    NUM_SCHEDULES = "num_schedules"
    SHAPE = "shape"  # shape of the results
    RESULTS = "results"


class LOOP:
    """Loop class and attribute names."""

    LOOP = "loop"
    PARAMETER = "parameter"
    ALIAS = "alias"
    CHANNEL_ID = "channel_id"
    PREVIOUS = "previous"
    VALUES = "values"


class NODE:
    """Chip node class and attribute names"""

    NODES = "nodes"
    FREQUENCY = "frequency"
    QUBIT_INDEX = "qubit_index"
    LINE = "line"


class PULSESCHEDULES:
    """Pulse Schedules attribute names."""

    ELEMENTS = "elements"


class PULSEBUSSCHEDULE:
    """PULSE BUS SCHEDULE attribute names."""

    TIMELINE = "timeline"
    PORT = "port"


class PULSE:
    """Pulse attribute names."""

    NAME = "name"
    AMPLITUDE = "amplitude"
    FREQUENCY = "frequency"
    PHASE = "phase"
    DURATION = "duration"
    PORT = "port"
    PULSE_SHAPE = "pulse_shape"


class PULSESHAPE:
    """PulseShape attribute names."""

    NAME = "name"


class PULSEDISTORTION:
    """PulsePredecessor attribute names."""

    NAME = "name"


class PULSEEVENT:
    """PulseEvent attribute names."""

    PULSE = "pulse"
    PULSE_DISTORTIONS = "pulse_distortions"
    START_TIME = "start_time"


class INSTRUMENTCONTROLLER:
    """Instrument controller attribute names."""

    CONNECTION = "connection"
    MODULES = "modules"
    RESET = "reset"


class CONNECTION:
    """Connection attribute names."""

    ADDRESS = "address"


class QBLOXRESULT:
    """Qblox Results attribute names."""

    INTEGRATION_LENGTHS = "integration_lengths"
    QBLOX_RAW_RESULTS = "qblox_raw_results"


class QBLOXMEASUREMENTRESULT:
    """Qblox Results attribute names."""

    RAW_MEASUREMENT_DATA = "raw_measurement_data"


class QMRESULT:
    """Quantum Machines Results attribute names."""

    I = "i"
    Q = "q"
    ADC1 = "adc1"
    ADC2 = "adc2"


class RESULTSDATAFRAME:
    """Results DataFrame Attributes"""

    SOFTWARE_AVG_INDEX = "software_avg_index"
    SEQUENCE_INDEX = "sequence_index"
    LOOP_INDEX = "loop_index_"
    QUBIT_INDEX = "qubit_index"
    RESULTS_INDEX = "results_index"
    BINS_INDEX = "bins_index"
    SCOPE_INDEX = "scope_index"
    ACQUISITION_INDEX = "acquisition_index"
    P0 = "p0"
    P1 = "p1"
    I = "i"  # noqa: E741
    Q = "q"
    AMPLITUDE = "amplitude"
    PHASE = "phase"


UNITS = {"frequency": "Hz"}

UNIT_PREFIX = {
    1e-24: "y",  # yocto
    1e-21: "z",  # zepto
    1e-18: "a",  # atto
    1e-15: "f",  # femto
    1e-12: "p",  # pico
    1e-9: "n",  # nano
    1e-6: "u",  # micro
    1e-3: "m",  # mili
    1e-2: "c",  # centi
    1e-1: "d",  # deci
    1e3: "k",  # kilo
    1e6: "M",  # mega
    1e9: "G",  # giga
    1e12: "T",  # tera
    1e15: "P",  # peta
    1e18: "E",  # exa
    1e21: "Z",  # zetta
    1e24: "Y",  # yotta
}


class QBLOXCONSTANTS:
    """Qblox Constants"""

    SCOPE_LENGTH = 16380
