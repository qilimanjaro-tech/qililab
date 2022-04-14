from dataclasses import dataclass

from qililab.settings.settings import Settings


@dataclass
class ResonatorSettings(Settings):
    """Contains the settings obtained from calibrating the qubit.

    Args:
        id (str): ID of the settings.
        name (str): Unique name of the settings.
        category (str): General name of the settings category. Options are "platform", "qubit_control",
        "qubit_readout", "signal_generator", "qubit", "resonator" and "schema".
    """

    pi_pulse_amplitude: float  # V
    pi_pulse_duration: float  # ns
    pi_pulse_frequency: float  # Hz
    qubit_frequency: float  # Hz
    min_voltage: float  # V
    max_voltage: float  # V
