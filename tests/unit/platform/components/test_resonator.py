import pytest

from qililab.platform import Resonator

from ...data import MockedSettingsHashTable


@pytest.fixture(name="resonator")
def fixture_resonator() -> Resonator:
    """Load Resonator.

    Returns:
        Resonator: Instance of the Resonator class.
    """
    resonator_settings = MockedSettingsHashTable.get("resonator_0")

    return Resonator(settings=resonator_settings)


class Testresonator:
    """Unit tests checking the Resonator attributes and methods."""

    def test_id_property(self, resonator: Resonator):
        """Test id property."""
        assert resonator.id_ == resonator.settings.id_

    def test_name_property(self, resonator: Resonator):
        """Test name property."""
        assert resonator.name == resonator.settings.name

    def test_category_property(self, resonator: Resonator):
        """Test name property."""
        assert resonator.category == resonator.settings.category

    def test_qubits_property(self, resonator: Resonator):
        """Test qubits property."""
        assert resonator.qubits == resonator.settings.qubits
