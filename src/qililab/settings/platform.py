from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class PlatformSettings(Settings):
    """Contains the settings of the platform.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator", "mixer" and "schema".
        number_qubits (int): Number of qubits used in the platform.
        hardware_average (int): Hardware average. Number of shots used when executing a sequence.
        software_average (float): Software average.
        repetition_duration (int): Duration (ns) of the whole program.
        delay_between_pulses (int): Delay (ns) between two consecutive pulses.
        drag_coefficient (float): Coefficient used for the drag pulse.
        number_of_sigmas (float): Number of sigmas that the pulse contains. sigma = pulse_duration / number_of_sigmas.
    """

    number_qubits: int
    hardware_average: int
    software_average: int
    repetition_duration: int  # ns
    delay_between_pulses: int  # ns
    delay_before_readout: int  # ns
    drag_coefficient: float
    number_of_sigmas: float
