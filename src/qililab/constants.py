"""Constants"""

# Environment variables
DATA = "DATA"  # variable containing the path where data is saved
RUNCARDS = "RUNCARDS"  # variable containing the runcard's path

RESULTS_FILENAME = "results.yml"
EXPERIMENT_FILENAME = "experiment.yml"

DEFAULT_PLATFORM_NAME = "galadriel"
GALADRIEL_DEVICE_ID = 9

DEFAULT_PLOT_Y_LABEL = "Sequence idx"


# TODO: Distribute constants over different classes


class RUNCARD:
    """YAML constants."""

    ID = "id_"
    NAME = "name"
    ALIAS = "alias"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    INSTRUMENT = "instrument"
    ELEMENTS = "elements"
    READOUT = "readout"
    SETTINGS = "settings"
    PLATFORM = "platform"
    SCHEMA = "schema"
    AWG = "awg"
    SIGNAL_GENERATOR = "signal_generator"
    ATTENUATOR = "attenuator"
    SYSTEM_CONTROL = "system_control"
    INSTRUMENT_CONTROLLER = "instrument_controller"
    FIRMWARE = "firmware"
    GATES = "gates"


class PLATFORM:
    """Platform attribute names."""

    DELAY_BETWEEN_PULSES = "delay_between_pulses"
    DELAY_BEFORE_READOUT = "delay_before_readout"
    MASTER_AMPLITUDE_GATE = "master_amplitude_gate"
    MASTER_DURATION_GATE = "master_duration_gate"


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
    NUM_SEQUENCES = "num_sequences"
    SEQUENCES = "sequences"
    LOOPS = "loops"


class SCHEMA:
    """Schema constants."""

    INSTRUMENTS = "instruments"
    BUSES = "buses"
    CHIP = "chip"
    INSTRUMENT_CONTROLLERS = "instrument_controllers"


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

    ELEMENTS = "elements"


class PULSESEQUENCE:
    """PulseSequence attribute names."""

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


class PULSEEVENT:
    """PulseEvent attribute names."""

    PULSE = "pulse"
    START_TIME = "start_time"


class INSTRUMENTCONTROLLER:
    """Instrument controller attribute names."""

    CONNECTION = "connection"
    MODULES = "modules"


class CONNECTION:
    """Connection attribute names."""

    ADDRESS = "address"


class INSTRUMENTREFERENCE:
    """InstrumentReference attribute names."""

    SLOT_ID = "slot_id"


class QBLOXRESULT:
    """Qblox Results attribute names."""

    PULSE_LENGTH = "pulse_length"
    QBLOX_RAW_RESULTS = "qblox_raw_results"


class RESULTSDATAFRAME:
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
    SCOPE_LENGTH = 16380
