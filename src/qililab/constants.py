"""Constants"""

# Environment variables
DATA = "DATA"  # variable containing the path where data is saved
RUNCARDS = "RUNCARDS"  # variable containing the runcard's path

RESULTS_FILENAME = "results.yml"
EXPERIMENT_FILENAME = "experiment.yml"
DATA_FOLDERNAME = "data"

DEFAULT_SETTINGS_FOLDERNAME = "qili"
DEFAULT_PLATFORM_NAME = "galadriel"


# TODO: Distribute constants over different classes
class YAML:
    """YAML constants."""

    ID = "id_"
    NAME = "name"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    INSTRUMENT = "instrument"
    ELEMENTS = "elements"
    READOUT = "readout"
    SETTINGS = "settings"
    PLATFORM = "platform"
    SCHEMA = "schema"
    SCHEMA = "schema"


class PLATFORM:
    """Platform constants."""

    TRANSLATION_SETTINGS = "translation_settings"


class EXPERIMENT:
    """Experiment constants."""

    HARDWARE_AVERAGE = "hardware_average"
    SOFTWARE_AVERAGE = "software_average"
    REPETITION_DURATION = "repetition_duration"
    SHAPE = "shape"
    RESULTS = "results"
    NUM_SEQUENCES = "num_sequences"
    SEQUENCES = "sequences"


class SCHEMA:
    """Schema constants."""

    INSTRUMENTS = "instruments"
    BUSES = "buses"


class BUS:
    """Bus constants."""

    PORT = "port"
    SYSTEM_CONTROL = "system_control"
    ATTENUATOR = "attenuator"
    SEQUENCES = "sequences"
    NUM_SEQUENCES = "num_sequences"
    SHAPE = "shape"  # shape of the results
    RESULTS = "results"


class LOOP:
    """Loop class and attribute names."""

    LOOP = "loop"
    PARAMETER = "parameter"
    START = "start"
    STOP = "stop"
    NUM = "num"
    STEP = "step"


class PULSESEQUENCES:
    """PulseSequenes attribute names."""

    PULSES = "pulses"
    TIME = "time"
    DELAY_BETWEEN_PULSES = "delay_between_pulses"
    DELAY_BEFORE_READOUT = "delay_before_readout"


class PULSE:
    """Pulse attribute names."""

    NAME = "name"
    AMPLITUDE = "amplitude"
    PHASE = "phase"
    DURATION = "duration"
    QUBIT_IDS = "qubit_ids"
    PULSE_SHAPE = "pulse_shape"
    START_TIME = "start_time"


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
