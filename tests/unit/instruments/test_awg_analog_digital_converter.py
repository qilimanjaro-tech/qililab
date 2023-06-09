"""This file tests the the ``AWGAnalogDigitalConverter`` class"""
from unittest.mock import MagicMock

import pytest

from qililab.constants import RUNCARD
from qililab.instruments import AWG, AWGAnalogDigitalConverter
from qililab.instruments.awg_settings.typings import AWGSequencerTypes, AWGTypes
from qililab.pulse import PulseBusSchedule
from qililab.typings.enums import AcquireTriggerMode, Category, InstrumentName, Parameter


class DummyAWG(AWGAnalogDigitalConverter):
    """Dummy AWG class."""

    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list:  # pylint disable=arguments-differ
        return []

    def run(self):
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
        RUNCARD.ID: 0,
        RUNCARD.ALIAS: InstrumentName.QBLOX_QCM.value,
        RUNCARD.CATEGORY: Category.AWG.value,
        "acquisition_delay_time": 100,
        RUNCARD.FIRMWARE: "0.7.0",
        Parameter.NUM_SEQUENCERS.value: 1,
        AWGTypes.AWG_SEQUENCERS.value: [
            {
                AWGSequencerTypes.IDENTIFIER.value: 0,
                AWGSequencerTypes.CHIP_PORT_ID.value: 0,
                "output_i": 0,
                "output_q": 1,
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
