from multiprocessing.sharedctypes import Value
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qililab import PLATFORM_MANAGER_DB, PLATFORM_MANAGER_YAML
from qililab.constants import DEFAULT_PLATFORM_NAME
from qililab.instruments import Mixer, QubitControl, QubitReadout, SignalGenerator
from qililab.platform import Buses, Platform, Qubit, Resonator, Schema
from qililab.typings import Category

from ..utils.side_effect import yaml_safe_load_side_effect


def platform_db():
    """Return PlatformBuilderDB instance with loaded platform."""
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_DB.build(platform_name="platform_0")
        mock_load.assert_called()
    return platform


def platform_yaml():
    """Return PlatformBuilderYAML instance with loaded platform."""
    filepath = Path(__file__).parent.parent.parent.parent / "examples" / "all_platform.yml"
    with patch("qililab.settings.settings_manager.yaml.safe_load", side_effect=yaml_safe_load_side_effect) as mock_load:
        platform = PLATFORM_MANAGER_YAML.build(filepath=str(filepath))
        mock_load.assert_called()
    return platform


@patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
@patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
def connect_platform(mock_rs: MagicMock, mock_pulsar: MagicMock, platform: Platform):
    """Return connected platform"""
    # add dynamically created attributes
    mock_rs_instance = mock_rs.return_value
    mock_rs_instance.mock_add_spec(["power", "frequency"])
    mock_pulsar_instance = mock_pulsar.return_value
    mock_pulsar_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
        ]
    )
    mock_pulsar_instance.sequencer0.mock_add_spec(["sync_en", "gain_awg_path0", "gain_awg_path1", "sequence"])
    platform.connect()
    mock_rs.assert_called()
    mock_pulsar.assert_called()
    return platform


@pytest.mark.parametrize("platform", [platform_db(), platform_yaml()])
class TestPlatform:
    """Unit tests checking the Platform attributes and methods."""

    def test_id_property(self, platform: Platform):
        """Test id property."""
        assert platform.id_ == platform.settings.id_

    def test_name_property(self, platform: Platform):
        """Test name property."""
        assert platform.name == platform.settings.name

    def test_category_property(self, platform: Platform):
        """Test name property."""
        assert platform.category == platform.settings.category

    def test_platform_name(self, platform: Platform):
        """Test platform name."""
        assert platform.name == DEFAULT_PLATFORM_NAME

    def test_get_element_method_schema(self, platform: Platform):
        """Test get_element method with schema."""
        assert isinstance(platform.get_element(category=Category.SCHEMA, id_=0), Schema)

    def test_get_element_method_buses(self, platform: Platform):
        """Test get_element method with buses."""
        assert isinstance(platform.get_element(category=Category.BUSES, id_=0), Buses)

    def test_connect_method_raises_error_when_already_connected(self, platform: Platform):
        """Test connect method raises error when already connected."""
        connect_platform(platform=platform)  # pylint: disable=no-value-for-parameter
        with pytest.raises(ValueError):
            platform.connect()

    def test_setup_method_raise_error(self, platform: Platform):
        """Test setup method raise error."""
        with pytest.raises(AttributeError):
            platform.setup()

    def test_setup_method(self, platform: Platform):
        """Test setup method."""
        connect_platform(platform=platform)  # pylint: disable=no-value-for-parameter
        platform.setup()
        # assert that the class attributes of different instruments are equal to the platform settings
        assert (
            platform.get_element(category=Category.QUBIT_INSTRUMENT, id_=0).hardware_average
            == platform.get_element(category=Category.QUBIT_INSTRUMENT, id_=0).hardware_average
            == platform.settings.hardware_average
        )

    def test_str_magic_method(self, platform: Platform):
        """Test __str__ magic method."""
        str(platform)

    def test_settings_instance(self, platform: Platform):
        """Test settings instance."""
        assert isinstance(platform.settings, Platform.PlatformSettings)

    def test_schema_instance(self, platform: Platform):
        """Test schema instance."""
        assert isinstance(platform.schema, Schema)

    def test_buses_instance(self, platform: Platform):
        """Test buses instance."""
        assert isinstance(platform.buses, Buses)

    def test_bus_0_signal_generator_instance(self, platform: Platform):
        """Test bus 0 signal generator instance."""
        assert isinstance(platform.get_element(category=Category.SIGNAL_GENERATOR, id_=0), SignalGenerator)

    def test_bus_0_mixer_instance(self, platform: Platform):
        """Test bus 0 mixer instance."""
        assert isinstance(platform.get_element(category=Category.MIXER, id_=0), Mixer)

    def test_bus_0_resonator_instance(self, platform: Platform):
        """Test bus 0 resonator instance."""
        assert isinstance(platform.get_element(category=Category.RESONATOR, id_=0), Resonator)

    def test_bus_0_resonator_qubit_0_instance(self, platform: Platform):
        """Test bus 0 resonator qubit 0 instance."""
        assert isinstance(platform.get_element(category=Category.QUBIT, id_=0), Qubit)

    def test_bus_0_qubit_instrument_instance(self, platform: Platform):
        """Test bus 0 qubit control instance."""
        assert isinstance(platform.get_element(category=Category.QUBIT_INSTRUMENT, id_=0), QubitControl)

    def test_bus_1_qubit_instrument_instance(self, platform: Platform):
        """Test bus 1 qubit readout instance."""
        assert isinstance(platform.get_element(category=Category.QUBIT_INSTRUMENT, id_=1), QubitReadout)

    @patch("qililab.settings.settings_manager.yaml.safe_dump")
    def test_platform_manager_dump_method(self, mock_dump: MagicMock, platform: Platform):
        """Test PlatformManager dump method."""
        PLATFORM_MANAGER_DB.dump(platform=platform)
        mock_dump.assert_called()

    def test_platform_manager_yaml_build_method_without_kwarg(self, platform: Platform):
        """Test PlatformManagerYAML build method with wrong argument."""
        with pytest.raises(ValueError):
            PLATFORM_MANAGER_YAML.build(platform.name)

    def test_platform_manager_db_build_method_without_kwarg(self, platform: Platform):
        """Test PlatformManagerYAML build method with wrong argument."""
        with pytest.raises(ValueError):
            PLATFORM_MANAGER_DB.build(platform.name)
