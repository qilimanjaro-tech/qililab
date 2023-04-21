"""Tests for the QbloxQCM class."""
import copy
from unittest.mock import MagicMock, patch

import pytest
from qpysequence.acquisitions import Acquisitions
from qpysequence.program import Program
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instrument_controllers.qblox.qblox_pulsar_controller import QbloxPulsarController
from qililab.instruments import QbloxQCM
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter
from tests.data import Galadriel


@pytest.fixture(name="pulsar_controller_qcm")
def fixture_pulsar_controller_qcm(platform: Platform):
    """Return an instance of QbloxPulsarController class"""
    settings = copy.deepcopy(Galadriel.pulsar_controller_qcm_0)
    settings.pop("name")
    return QbloxPulsarController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="qcm_no_device")
def fixture_qcm_no_device():
    """Return an instance of QbloxQCM class"""
    settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    settings.pop("name")
    return QbloxQCM(settings=settings)


@pytest.fixture(name="qcm")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
def fixture_qcm(mock_pulsar: MagicMock, pulsar_controller_qcm: QbloxPulsarController):
    """Return connected instance of QbloxQCM class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "out0_offset",
            "out1_offset",
            "out2_offset",
            "out3_offset",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "scope_acq_sequencer_select",
        ]
    )
    mock_instance.sequencers = [mock_instance.sequencer0]
    mock_instance.sequencer0.mock_add_spec(
        [
            "sync_en",
            "gain_awg_path0",
            "gain_awg_path1",
            "sequence",
            "mod_en_awg",
            "nco_freq",
            "scope_acq_sequencer_select",
            "channel_map_path0_out0_en",
            "channel_map_path1_out1_en",
            "demod_en_acq",
            "integration_length_acq",
            "set",
            "mixer_corr_phase_offset_degree",
            "mixer_corr_gain_ratio",
            "offset_awg_path0",
            "offset_awg_path1",
        ]
    )
    pulsar_controller_qcm.connect()
    return pulsar_controller_qcm.modules[0]


@pytest.fixture(name="big_pulse_bus_schedule")
def fixture_big_pulse_bus_schedule() -> PulseBusSchedule:
    """Load PulseBusSchedule with 10 different frequencies.

    Returns:
        PulseBusSchedule: PulseBusSchedule with 10 different frequencies.
    """
    timeline = [
        PulseEvent(
            pulse=Pulse(
                amplitude=1,
                phase=0,
                duration=1000,
                frequency=7.0e9 + n * 0.1e9,
                pulse_shape=Gaussian(num_sigmas=5),
            ),
            start_time=0,
        )
        for n in range(10)
    ]
    return PulseBusSchedule(timeline=timeline, port=0)


class TestQbloxQCM:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_inital_setup_method(self, qcm: QbloxQCM):
        """Test initial_setup method"""
        qcm.initial_setup()
        qcm.device.out0_offset.assert_called()
        qcm.device.out1_offset.assert_called()
        qcm.device.out2_offset.assert_called()
        qcm.device.out3_offset.assert_called()
        qcm.device.sequencer0.sync_en.assert_called_with(qcm.awg_sequencers[0].sync_enabled)
        qcm.device.sequencer0.mod_en_awg.assert_called()
        qcm.device.sequencer0.offset_awg_path0.assert_called()
        qcm.device.sequencer0.offset_awg_path1.assert_called()
        qcm.device.sequencer0.mixer_corr_gain_ratio.assert_called()
        qcm.device.sequencer0.mixer_corr_phase_offset_degree.assert_called()

    def test_start_sequencer_method(self, qcm: QbloxQCM):
        """Test start_sequencer method"""
        qcm.start_sequencer()
        qcm.device.arm_sequencer.assert_called()
        qcm.device.start_sequencer.assert_called()

    @pytest.mark.parametrize(
        "parameter, value, channel_id",
        [
            (Parameter.GAIN, 0.02, 0),
            (Parameter.GAIN_PATH0, 0.03, 0),
            (Parameter.GAIN_PATH1, 0.01, 0),
            (Parameter.OFFSET_I, 0.9, 0),
            (Parameter.OFFSET_Q, 0.12, 0),
            (Parameter.OFFSET_OUT0, 1.234, None),
            (Parameter.OFFSET_OUT1, 0, None),
            (Parameter.OFFSET_OUT2, 0.123, None),
            (Parameter.OFFSET_OUT3, 10, None),
            (Parameter.OFFSET_PATH0, 0.8, 0),
            (Parameter.OFFSET_PATH1, 0.11, 0),
            (Parameter.IF, 100_000, 0),
            (Parameter.HARDWARE_MODULATION, True, 0),
            (Parameter.HARDWARE_MODULATION, False, 0),
            (Parameter.SYNC_ENABLED, False, 0),
            (Parameter.SYNC_ENABLED, True, 0),
            (Parameter.NUM_BINS, 1, 0),
            (Parameter.GAIN_IMBALANCE, 0.1, 0),
            (Parameter.PHASE_IMBALANCE, 0.09, 0),
        ],
    )
    def test_setup_method(self, parameter: Parameter, value: float | bool | int, channel_id: int, qcm: QbloxQCM):
        """Test setup method"""
        qcm.setup(parameter=parameter, value=value, channel_id=channel_id)
        if parameter == Parameter.GAIN:
            assert qcm.awg_sequencers[channel_id].gain_path0 == value
            assert qcm.awg_sequencers[channel_id].gain_path1 == value
        if parameter == Parameter.GAIN_PATH0:
            assert qcm.awg_sequencers[channel_id].gain_path0 == value
        if parameter == Parameter.GAIN_PATH1:
            assert qcm.awg_sequencers[channel_id].gain_path1 == value
        if parameter == Parameter.OFFSET_I:
            assert qcm.offset_i(sequencer_id=channel_id) == value
        if parameter == Parameter.OFFSET_Q:
            assert qcm.offset_q(sequencer_id=channel_id) == value
        if parameter == Parameter.OFFSET_PATH0:
            assert qcm.awg_sequencers[channel_id].offset_path0 == value
        if parameter == Parameter.OFFSET_PATH1:
            assert qcm.awg_sequencers[channel_id].offset_path1 == value
        if parameter == Parameter.IF:
            assert qcm.awg_sequencers[channel_id].intermediate_frequency == value
        if parameter == Parameter.HARDWARE_MODULATION:
            assert qcm.awg_sequencers[channel_id].hardware_modulation == value
        if parameter == Parameter.SYNC_ENABLED:
            assert qcm.awg_sequencers[channel_id].sync_enabled == value
        if parameter == Parameter.NUM_BINS:
            assert qcm.awg_sequencers[channel_id].num_bins == value
        if parameter == Parameter.GAIN_IMBALANCE:
            assert qcm.awg_sequencers[channel_id].gain_imbalance == value
        if parameter == Parameter.PHASE_IMBALANCE:
            assert qcm.awg_sequencers[channel_id].phase_imbalance == value
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            assert qcm.out_offsets[output] == value

    def test_setup_out_offset_raises_error(self, qcm: QbloxQCM):
        """Test that calling ``_set_out_offset`` with a wrong output value raises an error."""
        with pytest.raises(IndexError, match="Output 5 is out of range"):
            qcm._set_out_offset(output=5, value=1)

    def test_turn_off_method(self, qcm: QbloxQCM):
        """Test turn_off method"""
        qcm.turn_off()
        qcm.device.stop_sequencer.assert_called_once()

    def test_reset_method(self, qcm: QbloxQCM):
        """Test reset method"""
        qcm._cache = {0: None}  # type: ignore # pylint: disable=protected-access
        qcm.reset()
        assert qcm._cache == {}  # pylint: disable=protected-access

    def test_compile(self, qcm, pulse_bus_schedule):
        """Test compile method."""
        sequences = qcm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=2000)
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert sequences[0]._program.duration == 1000 * 2000 + 4

    def test_upload_raises_error(self, qcm):
        """Test upload method raises error."""
        with pytest.raises(ValueError, match="Please compile the circuit before uploading it to the device"):
            qcm.upload()

    def test_upload_method(self, qcm, pulse_bus_schedule):
        """Test upload method"""
        qcm.compile(pulse_bus_schedule, nshots=1000, repetition_duration=100)
        qcm.upload()
        qcm.device.sequencer0.sequence.assert_called_once()

    def test_id_property(self, qcm_no_device: QbloxQCM):
        """Test id property."""
        assert qcm_no_device.id_ == qcm_no_device.settings.id_

    def test_name_property(self, qcm_no_device: QbloxQCM):
        """Test name property."""
        assert qcm_no_device.name == InstrumentName.QBLOX_QCM

    def test_category_property(self, qcm_no_device: QbloxQCM):
        """Test category property."""
        assert qcm_no_device.category == qcm_no_device.settings.category

    def test_firmware_property(self, qcm_no_device: QbloxQCM):
        """Test firmware property."""
        assert qcm_no_device.firmware == qcm_no_device.settings.firmware

    def test_max_frequencies_error(self, qcm: QbloxQCM, big_pulse_bus_schedule: PulseBusSchedule):
        """Test split_schedule_for_sequencers method raises error when handling more frequencies than it can support."""
        expected_error_message = f"The number of frequencies must be less or equal than {qcm._NUM_MAX_SEQUENCERS}"
        with pytest.raises(IndexError, match=expected_error_message):
            qcm._split_schedule_for_sequencers(pulse_bus_schedule=big_pulse_bus_schedule)

    def test_compile_not_single_freq_error(self, qcm: QbloxQCM, big_pulse_bus_schedule: PulseBusSchedule):
        """Test that the compile method raises an error when the PulseBusSchedule contains more than one frequency."""
        expected_error_message = f"The PulseBusSchedule of a sequencer must have exactly one frequency. This instance has {len(big_pulse_bus_schedule.frequencies())}."
        with pytest.raises(ValueError, match=expected_error_message):
            qcm._compile(pulse_bus_schedule=big_pulse_bus_schedule, sequencer=0)
