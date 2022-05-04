"""ExperimentSettings class"""
from dataclasses import dataclass

# TODO: I moved this class inside the module settings/ to avoid circular imports,
# because it is used by both the Experiment and QubitInstrument classes.

# FIXME: We should find a better way to setup the QubitInstrument class attributes.
# Right now it is done by the Experiment object.


@dataclass
class ExperimentSettings:
    """Contains the settings that are generic for all QubitInstrument objects.

    Args:
        hardware_average (int): Hardware average. Number of shots used when executing a sequence.
        software_average (int): Software average.
        repetition_duration (int): Duration (ns) of the whole program.
        delay_between_pulses (int): Delay (ns) between two consecutive pulses.
    """

    hardware_average: int
    software_average: int
    repetition_duration: int
    delay_between_pulses: int
