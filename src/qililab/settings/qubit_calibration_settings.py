from dataclasses import dataclass

from qililab.settings import AbstractSettings


# TODO: Create parent class CalibrationSettings. What should be the difference from AbstractSettings?
@dataclass
class QubitCalibrationSettings(AbstractSettings):
    """Contains the settings obtained from calibrating the qubit.

    Args:
        pi_pulse_amplitude (float): Voltage amplitude (in V) used to generate a pi pulse.
        pi_pulse_duration (float): Duration of the pi pulse.
        pi_pulse_freq (float): Frequency of the pi pulse.
        qubit_freq (float): Frequency of the qubit.
        min_voltage (float): Minimum voltage obtained on a rabi oscillation.
        max_voltage (float): Maximum voltage obtained on a rabi oscillation.
    """

    pi_pulse_amplitude: float  # V
    pi_pulse_duration: float  # ns
    pi_pulse_frequency: float  # Hz
    qubit_freq: float  # Hz
    min_voltage: float  # V
    max_voltage: float  # V
