from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class PlatformSettings(Settings):
    """Contains the settings of the platform.

    Args:
        n_qubits (int): Number of qubits.
        hw_avg (int): Hardware average. Number of shots used when executing a sequence.
        sw_avg (float): Software average.
    """

    number_qubits: int
    hardware_average: int
    software_average: int
    repetition_duration: int  # ns
    delay_between_pulses: int  # ns
    delay_before_readout: int  # ns
    drag_coefficient: float
    number_of_sigmas: float
