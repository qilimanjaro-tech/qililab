"""Constants"""
DEFAULT_PLATFORM_FILENAME = "platform.yml"
DEFAULT_SETTINGS_FOLDERNAME = "qili"
DEFAULT_RUNCARD_FILENAME = "runcard.yml"
DEFAULT_PLATFORM_NAME = "platform_0"


class YAML:
    """YAML constants."""

    ID = "id_"
    NAME = "name"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    ELEMENTS = "elements"
    READOUT = "readout"
    SETTINGS = "settings"
    HARDWARE_AVERAGE = "hardware_average"
    SOFTWARE_AVERAGE = "software_average"
    REPETITION_DURATION = "repetition_duration"
    SCHEMA = "schema"
    PORT = "port"


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
