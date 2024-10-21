import pytest
from unittest import mock
from qililab.typings.enums import ConnectionName, InstrumentControllerName
from qililab.instruments.keithley.keithley_2600 import Keithley2600
from qililab.instrument_controllers.utils.instrument_controller_factory import InstrumentControllerFactory
from qililab.instruments.instruments import Instruments
from qililab.typings import Keithley2600Driver
from tests.instruments.keithley.test_keithley_2600 import keithley2600


@pytest.fixture
def mock_device():
    """Mock the Keithley2600Driver with autospec to ensure it's realistic."""
    return mock.create_autospec(Keithley2600Driver, spec_set=True)


@pytest.fixture
def settings():
    """Fixture for the controller settings, using autospec."""
    settings = {
        "alias": "keithley_controller",
        "connection": {
            "name": "tcp_ip",
            "address": "192.168.0.1"
        },
        "modules": [{
            "alias": "keithley",
            "slot_id": 0
        }]
    }
    return settings


@pytest.fixture
def keithley_controller(settings, keithley2600):
    """Fixture to initialize the Keithley2600Controller with mocked device and settings."""
    instruments = Instruments(elements=[keithley2600])

    Keithley2600Controller = InstrumentControllerFactory.get(InstrumentControllerName.KEITHLEY2600)
    controller = Keithley2600Controller(settings=settings, loaded_instruments=instruments)
    controller.device = mock.create_autospec(Keithley2600Driver, spec_set=True)

    return controller


class TestKeithley2600Controller:

    def test_initialize_device(self, keithley_controller, settings):
        """Test that the _initialize_device method sets up the device correctly."""
        keithley_controller._initialize_device()

        assert keithley_controller.device is not None
        keithley_controller.device.__init__.assert_called_with(
            name=f"{keithley_controller.name.value}_{keithley_controller.settings.alias}",
            address=f"TCPIP0::{keithley_controller.settings.address}::INSTR",
            visalib="@py"
        )

    def test_initialize_device_address(self, keithley_controller, settings):
        """Test that the device address is correctly set based on the settings."""
        keithley_controller._initialize_device()

        expected_address = f"TCPIP0::{settings.address}::INSTR"
        assert keithley_controller.device.address == expected_address

    def test_check_supported_modules_valid(self, keithley_controller):
        """Test that the _check_supported_modules method passes with valid modules."""
        # Create mock Keithley2600 instrument
        valid_module = mock.Mock(spec=Keithley2600)

        # Assign the mock module to the controller's modules
        keithley_controller.modules = [valid_module]

        # The function should not raise any exceptions for valid modules
        keithley_controller._check_supported_modules()

    def test_check_supported_modules_invalid(self, keithley_controller):
        """Test that the _check_supported_modules method raises an exception for unsupported modules."""
        # Create a mock instrument of the wrong type
        invalid_module = mock.Mock(spec=SingleInstrumentController)

        # Assign the invalid module to the controller's modules
        keithley_controller.modules = [invalid_module]

        # The function should raise a ValueError for unsupported modules
        with pytest.raises(ValueError, match="Instrument .* not supported."):
            keithley_controller._check_supported_modules()

    def test_controller_settings_post_init(self, keithley_controller, settings):
        """Test that the settings post_init method correctly sets the connection name."""
        assert keithley_controller.settings.connection.name == ConnectionName.TCP_IP
