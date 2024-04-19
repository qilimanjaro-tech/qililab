"""This file tests the the ``AWGAnalogDigitalConverter`` class"""
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from qpysequence import Sequence as QpySequence

from qililab.constants import RUNCARD
from qililab.instruments import AWG, AWGAnalogDigitalConverter
from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.awg_settings.typings import AWGSequencerTypes, AWGTypes
from qililab.pulse import PulseBusSchedule
from qililab.typings.enums import AcquireTriggerMode, InstrumentName, Parameter


class DummyAWG(AWGAnalogDigitalConverter):
    """Dummy AWG class."""

    def compile(  # pylint: disable=unused-argument
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list:
        return []

    def run(self):  # pylint: disable=arguments-differ
        pass

    def upload(self, port: str):
        pass

    def upload_qpysequence(self, qpysequence: QpySequence, port: str):
        pass

    def acquire_result(self):
        return []

    def _set_device_scope_hardware_averaging(self, value: bool, sequencer_id: int):
        pass

    def _set_device_threshold(self, value: float, sequencer_id: int):
        pass

    def _set_device_threshold_rotation(self, value: float, sequencer_id: int):
        pass

    def _set_device_hardware_demodulation(self, value: bool, sequencer_id: int):
        pass

    def _set_device_acquisition_mode(self, mode: AcquireTriggerMode, sequencer_id: int):
        pass

    def _set_device_integration_length(self, value: int, sequencer_id: int):
        pass


@pytest.fixture(name="awg")
def fixture_awg():
    """Fixture that returns an instance of a dummy AWG."""
    settings = {
        RUNCARD.ALIAS: InstrumentName.QBLOX_QCM.value,
        "acquisition_delay_time": 100,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 0,
                "outputs": [0, 1],
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
            }
        ],
    }
    return DummyAWG(settings=settings)  # pylint: disable=abstract-class-instantiated


class TestAWGAnalogDigitalConverter:
    """This class contains the unit tests for the ``AWGAnalogDigitalConverte`` class."""

    def test_error_raises_when_no_channel_specified(self, awg: AWG):
        """These test makes soure that an error raises whenever a channel is not specified in chainging a parameter

        Args:
            awg (AWG): _description_
        """
        awg.settings.num_sequencers = 2
        with pytest.raises(ValueError, match="channel not specified to update instrument"):
            awg.device = MagicMock()
            awg.setup(parameter=Parameter.ACQUISITION_DELAY_TIME, value=2, channel_id=None)

    def test_setup_threshold(self, awg: AWG):
        """Test that calling `setup` with the `THRESHOLD` parameter works correctly."""
        awg.device = MagicMock()
        with patch.object(target=AWGAnalogDigitalConverter, attribute="_set_threshold") as mock_set:
            awg.setup(parameter=Parameter.THRESHOLD, value=2)
            mock_set.assert_called_once_with(value=2, sequencer_id=0)
            awg.device.assert_not_called()

    def test_setup_threshold_no_connection(self, awg: AWG):
        """Test that calling `setup` with the `THRESHOLD` parameter works correctly."""
        awg.device = None
        awg.setup(parameter=Parameter.THRESHOLD, value=2)
        assert cast(AWGADCSequencer, awg.get_sequencer(sequencer_id=0)).threshold == 2

    def test_setup_threshold_rotation(self, awg: AWG):
        """Test that calling `setup` with the `THRESHOLD_ROTATION` parameter works correctly."""
        awg.device = MagicMock()
        with patch.object(target=AWGAnalogDigitalConverter, attribute="_set_threshold_rotation") as mock_set:
            awg.setup(parameter=Parameter.THRESHOLD_ROTATION, value=2)
            mock_set.assert_called_once_with(value=2, sequencer_id=0)
            awg.device.assert_not_called()
