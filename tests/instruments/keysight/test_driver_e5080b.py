"""Tests for the DriverE5080B class."""

# This test along the driver code are meant to be qcodes

import copy
from unittest.mock import MagicMock, patch

import pytest

from qililab.instruments.keysight.driver_keysight_e5080b import Driver_KeySight_E5080B
from unittest import mock
import pyvisa
import pytest
from unittest import mock
from qililab.instruments.keysight.driver_keysight_e5080b import Driver_KeySight_E5080B
import pytest
from unittest import mock
from qililab.instruments.keysight.driver_keysight_e5080b import Driver_KeySight_E5080B

# Mocking pyvisa's ResourceManager and GPIBInstrument
@mock.patch('qcodes.instrument.visa.VisaInstrument._visa_handle')
def test_start_stop_freq(mock_visa_handle):
    # Mock the methods that interact with the instrument via VISA (write and query)
    mock_visa_handle.query.return_value = '1e6'  # Simulating a response for query
    mock_visa_handle.write.return_value = None  # Simulating successful write

    # Create the driver object without needing actual hardware
    driver = Driver_KeySight_E5080B('E5080B', 'GPIB::1::INSTR')

    # Test setting start and stop frequencies
    driver.start_freq(1e6)  # Setting start frequency to 1e6 Hz
    driver.stop_freq(1e9)   # Setting stop frequency to 1e9 Hz

    # Ensure the write command is called for both start and stop frequencies
    driver.visa_handle.write.assert_any_call('SENS:FREQ:STAR 1000000.0')
    driver.visa_handle.write.assert_any_call('SENS:FREQ:STOP 1000000000.0')

    # Verify the values were set correctly
    assert driver.start_freq() == 1e6
    assert driver.stop_freq() == 1e9

# Another example for center frequency
@mock.patch('qcodes.instrument.visa.VisaInstrument._visa_handle')
def test_center_freq(mock_visa_handle):
    # Mock the visa_handle's query method
    mock_visa_handle.query.return_value = '5e9'  # Simulating response for query

    # Create the driver object
    driver = Driver_KeySight_E5080B('E5080B', 'GPIB::1::INSTR')

    # Set the center frequency
    driver.center_freq(5e9)  # Setting center frequency to 5 GHz

    # Verify the write command was issued for setting center frequency
    driver.visa_handle.write.assert_any_call('SENS:FREQ:CENT 5000000000.0')

    # Ensure that the center frequency is set correctly
    assert driver.center_freq() == 5e9


# Additional tests can follow this pattern for other parameters

if __name__ == '__main__':
    pytest.main()
