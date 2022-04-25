"""Qubit class"""
from qililab.settings import QubitCalibrationSettings


class Qubit:
    """Qubit class"""

    def __init__(self, settings: dict):
        self.settings = QubitCalibrationSettings(**settings)

    @property
    def id_(self):
        """Qubit 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Qubit 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Qubit 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

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
