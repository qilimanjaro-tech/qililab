"""Qubit class"""
from typing import Union

from qililab.platform.components.bus_target.bus_target import BusTarget
from qililab.settings import Settings
from qililab.typings import BusElementName
from qililab.utils import Factory, nested_dataclass


@Factory.register
class Qubit(BusTarget):
    """Qubit class"""

    name = BusElementName.QUBIT

    @nested_dataclass
    class QubitCalibrationSettings(Settings):
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
        qubit_frequency: float  # Hz
        min_voltage: float  # V
        max_voltage: float  # V

    settings: QubitCalibrationSettings

    def __init__(self, settings: dict):
        self.settings = self.QubitCalibrationSettings(**settings)

    @property
    def qubit_ids(self):
        """Resonator 'qubit_ids' property.

        Returns:
            List[int]: List containing the IDs of the qubits connected to the resonator.
        """
        return [self.id_]

    @property
    def pi_pulse_amplitude(self):
        """Qubit 'pi_pulse_amplitude' property.

        Returns:
            float: settings.pi_pulse_amplitude.
        """
        return self.settings.pi_pulse_amplitude

    @property
    def pi_pulse_duration(self):
        """Qubit 'pi_pulse_duration' property.

        Returns:
            float: settings.pi_pulse_duration.
        """
        return self.settings.pi_pulse_duration

    @property
    def pi_pulse_frequency(self):
        """Qubit 'pi_pulse_frequency' property.

        Returns:
            float: settings.pi_pulse_frequency.
        """
        return self.settings.pi_pulse_frequency

    @property
    def qubit_frequency(self):
        """Qubit 'qubit_frequency' property.

        Returns:
            float: settings.qubit_frequency.
        """
        return self.settings.qubit_frequency

    @property
    def min_voltage(self):
        """Qubit 'min_voltage' property.

        Returns:
            float: settings.min_voltage.
        """
        return self.settings.min_voltage

    @property
    def max_voltage(self):
        """Qubit 'max_voltage' property.

        Returns:
            float: settings.max_voltage.
        """
        return self.settings.max_voltage

    def get_qubit(self, id_: int) -> Union["Qubit", None]:
        """Return specific Qubit class. Return None if qubit is not found.

        Args:
            id_ (int): ID of the qubit.

        Returns:
            (Qubit | None): Qubit class.
        """
        return self if self.id_ == id_ else None
