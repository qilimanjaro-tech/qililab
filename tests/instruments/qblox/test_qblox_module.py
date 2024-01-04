"""Tests for the Qblox Module class."""
import copy
import re
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab.instrument_controllers.qblox.qblox_pulsar_controller import QbloxPulsarController
from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxModule, QbloxQCM, QbloxQRM
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseSchedule
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.qblox_compiler import QbloxCompiler
from qililab.typings.enums import Parameter
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard=Galadriel.runcard)


class DummyQRM(QbloxQRM):
    """Dummy QRM class for testing"""

    _MIN_WAIT_TIME = 4

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.device = MagicMock()
        self.device.module_type.return_value = "QRM"


class DummyQCM(QbloxQCM):
    """Dummy QCM class for testing"""

    _MIN_WAIT_TIME = 4

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.device = MagicMock()
        self.device.module_type.return_value = "QCM"


@pytest.fixture(name="pulsar_controller_qrm")
def fixture_pulsar_controller_qrm():
    """Return an instance of QbloxPulsarController class"""
    platform = build_platform(runcard=Galadriel.runcard)
    settings = copy.deepcopy(Galadriel.pulsar_controller_qrm_0)
    settings.pop("name")
    return QbloxPulsarController(settings=settings, loaded_instruments=platform.instruments)


@pytest.fixture(name="qrm")
@patch("qililab.instrument_controllers.qblox.qblox_pulsar_controller.Pulsar", autospec=True)
def fixture_qrm(mock_pulsar: MagicMock, pulsar_controller_qrm: QbloxPulsarController):
    """Return connected instance of QbloxQRM class"""
    # add dynamically created attributes
    mock_instance = mock_pulsar.return_value
    mock_instance.mock_add_spec(
        [
            "reference_source",
            "sequencer0",
            "sequencer1",
            "out0_offset",
            "out1_offset",
            "scope_acq_trigger_mode_path0",
            "scope_acq_trigger_mode_path1",
            "scope_acq_sequencer_select",
            "scope_acq_avg_mode_en_path0",
            "scope_acq_avg_mode_en_path1",
            "get_acquisitions",
        ]
    )
    mock_instance.sequencers = [mock_instance.sequencer0, mock_instance.sequencer1]
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
            "thresholded_acq_threshold",
            "thresholded_acq_rotation",
            "marker_ovr_en",
            "marker_ovr_value",
        ]
    )
    # connect to instrument
    pulsar_controller_qrm.connect()
    return pulsar_controller_qrm.modules[0]


@pytest.fixture(name="qblox_compiler")
def fixture_qblox_compiler(platform: Platform, qrm):
    """Return an instance of QbloxModule class"""
    platform.instruments.elements = [qrm]
    return QbloxCompiler(platform)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    return PulseBusSchedule(timeline=[pulse_event], port="feedline_input")


@pytest.fixture(name="pulse_bus_schedule2")
def fixture_pulse_bus_schedule2() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=1)
    return PulseBusSchedule(timeline=[pulse_event], port="feedline_input")


class TestQbloxModule:  # pylint: disable=too-few-public-methods
    """Unit tests checking the QbloxModule attributes and methods"""

    def test_upload_method(self, qrm, qblox_compiler, pulse_bus_schedule):
        """Test that upload method uploads the sequences compiled at compiler."""
        pulse_schedule = PulseSchedule([pulse_bus_schedule])
        sequences = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "feedline_input_output_bus"
        ]
        qrm.upload(port=pulse_bus_schedule.port)
        assert qrm.sequences[0] is sequences[0]

        qrm.device.sequencers[0].sequence.assert_called_once()
        qrm.device.sequencers[0].sync_en.assert_called_once_with(True)
        qrm.device.sequencers[1].sequence.assert_not_called()

    def test_upload_pops_not_in_cache(self, qrm, qblox_compiler, pulse_bus_schedule, pulse_bus_schedule2):
        """Tests that uploading twice the same sequence for different qubit erases old sequences in the
        same busnot being used"""
        pulse_schedule = PulseSchedule([pulse_bus_schedule])
        pulse_schedule2 = PulseSchedule([pulse_bus_schedule2])

        sequences1 = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "feedline_input_output_bus"
        ]
        qrm.upload(port=pulse_bus_schedule.port)
        assert qrm.sequences[0] is sequences1[0]
        sequences2 = qblox_compiler.compile(pulse_schedule2, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "feedline_input_output_bus"
        ]
        qrm.upload(port=pulse_bus_schedule.port)
        # sequences2 qubit index is 1
        assert qrm.sequences[1] is sequences2[0]

    def test_num_sequencers_error(self):
        """test that an error is raised if more than _NUM_MAX_SEQUENCERS are in the qblox module"""

        nsequencers = 100
        settings = copy.deepcopy(Galadriel.qblox_qcm_0)
        settings.pop("name")
        settings["num_sequencers"] = nsequencers
        error_string = re.escape(
            "The number of sequencers must be greater than 0 and less or equal than "
            + f"{QbloxModule._NUM_MAX_SEQUENCERS}. Received: {nsequencers}"  # pylint: disable=protected-access
        )
        with pytest.raises(ValueError, match=error_string):
            QbloxModule(settings)

    def test_incorrect_num_sequencers_error(self):
        """test that an error is raised if num_sequencers is not the same as len(awg_sequencers)"""
        nsequencers = 2
        settings = copy.deepcopy(Galadriel.qblox_qcm_0)
        settings.pop("name")
        settings["num_sequencers"] = nsequencers
        settings["awg_sequencers"] = [settings["awg_sequencers"][0]]
        error_string = re.escape(
            f"The number of sequencers: {nsequencers} does not match "
            + "the number of AWG Sequencers settings specified: 1"
        )
        with pytest.raises(ValueError, match=error_string):
            QbloxModule(settings)

    def test_module_type(self):
        qrm_settings = copy.deepcopy(Galadriel.qblox_qrm_0)
        qrm_settings.pop("name")
        qrm = DummyQRM(settings=qrm_settings)
        assert qrm.module_type == "QRM"

    def test_setup_raises_error(self):
        qcm_settings = copy.deepcopy(Galadriel.qblox_qcm_0)
        qcm_settings.pop("name")
        qcm = DummyQCM(settings=qcm_settings)
        param = Parameter.NUM_BINS
        error_string = re.escape(f"Cannot update parameter {param.value} without specifying a channel_id.")
        with pytest.raises(ParameterNotFound, match=error_string):
            qcm.setup(parameter=Parameter.NUM_BINS, value=10)

    def test_get_raises_error(self):
        qcm_settings = copy.deepcopy(Galadriel.qblox_qcm_0)
        qcm_settings.pop("name")
        qcm = DummyQCM(settings=qcm_settings)
        param = Parameter.NUM_BINS
        error_string = re.escape(f"Cannot update parameter {param.value} without specifying a channel_id.")
        with pytest.raises(ParameterNotFound, match=error_string):
            qcm.get(parameter=Parameter.NUM_BINS)

    def test_set_num_bins_raises_error(self):
        qcm_settings = copy.deepcopy(Galadriel.qblox_qcm_0)
        qcm_settings.pop("name")
        qcm = DummyQCM(settings=qcm_settings)
        value = float(qcm._MAX_BINS + 1)
        error_string = re.escape(f"Value {value} greater than maximum bins: {qcm._MAX_BINS}")
        with pytest.raises(ValueError, match=error_string):
            qcm._set_num_bins(value=value, sequencer_id=0)
