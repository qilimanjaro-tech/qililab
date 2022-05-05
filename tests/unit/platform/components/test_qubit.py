import pytest

from qililab.platform import Qubit
from qililab.typings import BusElementName

from ...data import MockedSettingsHashTable


@pytest.fixture(name="qubit")
def fixture_qubit() -> Qubit:
    """Load Qubit.

    Returns:
        Qubit: Instance of the Qubit class.
    """
    qubit_settings = MockedSettingsHashTable.get("resonator_0")["qubits"][0]

    return Qubit(settings=qubit_settings)


class Testqubit:
    """Unit tests checking the Qubit attributes and methods."""

    def test_id_property(self, qubit: Qubit):
        """Test id property."""
        assert qubit.id_ == qubit.settings.id_

    def test_name_property(self, qubit: Qubit):
        """Test name property."""
        assert qubit.name == BusElementName.QUBIT

    def test_category_property(self, qubit: Qubit):
        """Test name property."""
        assert qubit.category == qubit.settings.category

    def test_pi_pulse_amplitude_property(self, qubit: Qubit):
        """Test pi_pulse_amplitude property."""
        assert qubit.pi_pulse_amplitude == qubit.settings.pi_pulse_amplitude

    def test_pi_pulse_duration_property(self, qubit: Qubit):
        """Test pi_pulse_duration property."""
        assert qubit.pi_pulse_duration == qubit.settings.pi_pulse_duration

    def test_pi_pulse_frequency_property(self, qubit: Qubit):
        """Test pi_pulse_frequency property."""
        assert qubit.pi_pulse_frequency == qubit.settings.pi_pulse_frequency

    def test_qubit_frequency_property(self, qubit: Qubit):
        """Test qubit_frequency property."""
        assert qubit.qubit_frequency == qubit.settings.qubit_frequency

    def test_min_voltage_property(self, qubit: Qubit):
        """Test min_voltage property."""
        assert qubit.min_voltage == qubit.settings.min_voltage

    def test_max_voltage_property(self, qubit: Qubit):
        """Test max_voltage property."""
        assert qubit.max_voltage == qubit.settings.max_voltage
