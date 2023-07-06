"""Tests for the SequencerQCM class."""
# pylint: disable=protected-access
from textwrap import dedent
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qcodes import Instrument
from qpysequence.program import Program
from qpysequence.sequence import Sequence as QpySequence

from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm
from qililab.drivers.instruments.qblox.sequencer_qcm import SequencerQCM
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

from .mock_utils import MockCluster, MockQcmQrm

PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name
NUM_SLOTS = 20
START_TIME_DEFAULT = 0
START_TIME_NON_ZERO = 4


def get_pulse_bus_schedule(start_time: int, negative_amplitude: bool = False, number_pulses: int = 1):
    """Returns a gaussian pulse bus schedule"""

    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=(-1 * PULSE_AMPLITUDE) if negative_amplitude else PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=start_time)
    timeline = [pulse_event for _ in range(number_pulses)]

    return PulseBusSchedule(timeline=timeline, port=0)


def get_envelope():
    """Returns a gaussian pulse bus schedule envelope"""

    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )

    return pulse.envelope()


expected_program_str_0 = repr(
    "setup:\n    move             1, R0\n    wait_sync        4\n\naverage:\n    move             0, R1\n    bin:\n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        long_wait_1:\n            wait             996\n\n        add              R1, 1, R1\n        nop\n        jlt              R1, 1, @bin\n    loop             R0, @average\nstop:\n    stop\n\n"
)
expected_program_str_1 = repr(
    "setup:\n    move             1, R0\n    wait_sync        4\n\naverage:\n    move             0, R1\n    bin:\n        long_wait_2:\n            wait             4\n\n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        long_wait_3:\n            wait             992\n\n        add              R1, 1, R1\n        nop\n        jlt              R1, 1, @bin\n    loop             R0, @average\nstop:\n    stop\n\n"
)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""

    return get_pulse_bus_schedule(start_time=0)


@pytest.fixture(name="pulse_bus_schedule_repeated_pulses")
def fixture_pulse_bus_schedule_repeated_pulses() -> PulseBusSchedule:
    """Return PulseBusSchedule instance with same pulse repeated."""

    return get_pulse_bus_schedule(start_time=0, number_pulses=3)


@pytest.fixture(name="pulse_bus_schedule_negative_amplitude")
def fixture_pulse_bus_schedule_negative_amplitude() -> PulseBusSchedule:
    """Return PulseBusSchedule instance with same pulse repeated."""

    return get_pulse_bus_schedule(start_time=0, negative_amplitude=True)


class TestSequencer:
    """Unit tests checking the Sequencer attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        cls.old_qcm_qrm_bases = QcmQrm.__bases__
        cls.old_cluster_bases = Cluster.__bases__
        QcmQrm.__bases__ = (MockQcmQrm,)
        Cluster.__bases__ = (MockCluster,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()
        QcmQrm.__bases__ = cls.old_qcm_qrm_bases
        Cluster.__bases__ = cls.old_cluster_bases

    def test_init(self):
        """Unit tests for init method"""

        sequencer_name = "test_sequencer_init"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        assert sequencer.get("swap_paths") is False

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._map_outputs")
    @pytest.mark.parametrize("path0", [0, 1])
    def test_set_with_qililab_path(self, mock_map_outputs: MagicMock, path0: int):
        """Unit tests for set method with qililab path"""

        sequencer_name = "test_sequencer_set_qililab_path"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequencer.set("path0", path0)
        mock_map_outputs.assert_called_once_with("path0", path0)

    def test_set_with_qblox_parameter(self):
        """Unit tests for set method with qblox parameter"""

        sequencer_name = "test_sequencer_set_qblox_parameter"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequencer.set("channel_map_path0_out0_en", True)
        assert sequencer.get("channel_map_path0_out0_en") is True

    @pytest.mark.parametrize("path0", [0, 1, 10])
    def test_map_outputs(self, path0: int):
        """Unit tests for _map_outputs method"""

        sequencer_name = f"test_sequencer_map_outputs{path0}"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        if path0 == 10:
            error_str = f"Impossible path configuration detected. path0 cannot be mapped to output {path0}."
            with pytest.raises(ValueError, match=error_str):
                sequencer._map_outputs("path0", path0)
                assert sequencer.get("swap_paths") is False

        else:
            sequencer._map_outputs("path0", path0)
            if path0 == 0:
                assert sequencer.get("swap_paths") is False
            elif path0 == 1:
                assert sequencer.get("swap_paths") is True

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms(self, pulse_bus_schedule: PulseBusSchedule, path0: int):
        """Unit tests for _generate_waveforms method"""

        sequencer_name = f"test_sequencer_waveforms{path0}"
        seq_idx = 0
        label = pulse_bus_schedule.timeline[0].pulse.label()
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        envelope = get_envelope()
        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule).to_dict()
        waveforms_keys = list(waveforms.keys())

        assert len(waveforms) == 2 * len(pulse_bus_schedule.timeline)
        assert waveforms_keys[0] == f"{label}_I"
        assert waveforms_keys[1] == f"{label}_Q"

        if path0 % 2 != 0:
            # swapped waveforms should have I component all zeros
            assert np.all(waveforms[waveforms_keys[0]]["data"]) == 0
            # swapped waveforms should have Q component equal to gaussian pulse envelope
            assert np.alltrue(envelope == waveforms[waveforms_keys[1]]["data"])
        else:
            # swapped waveforms should have Q component all zeros
            assert np.all(waveforms[waveforms_keys[1]]["data"]) == 0
            # swapped waveforms should have Q component equal to gaussian pulse envelope
            assert np.alltrue(envelope == waveforms[waveforms_keys[0]]["data"])

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms_multiple_pulses(self, pulse_bus_schedule_repeated_pulses: PulseBusSchedule, path0: int):
        """Unit tests for _generate_waveforms method with repeated pulses"""

        sequencer_name = f"test_sequencer_waveforms{path0}"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule_repeated_pulses).to_dict()

        assert len(waveforms) == 2

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms_negative_amplitude(
        self, pulse_bus_schedule_negative_amplitude: PulseBusSchedule, path0: int
    ):
        """Unit tests for _generate_waveforms method with negative amplitude"""

        sequencer_name = f"test_sequencer_waveforms{path0}"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule_negative_amplitude).to_dict()

        print("waveforms: ", waveforms)
        assert len(waveforms) == 2

    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._generate_waveforms")
    @patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._generate_program")
    def test_translate_pulse_bus_schedule(
        self, mock_generate_program: MagicMock, mock_generate_waveforms: MagicMock, pulse_bus_schedule: PulseBusSchedule
    ):
        """Unit tests for _translate_pulse_bus_schedule method"""

        sequencer_name = "test_sequencer_translate_pulse_bus_schedule"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequence = sequencer._translate_pulse_bus_schedule(
            pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1
        )

        assert isinstance(sequence, QpySequence)
        mock_generate_waveforms.assert_called_once()
        mock_generate_program.assert_called_once()

    @pytest.mark.parametrize(
        "pulse_bus_schedule, name, expected_program_str",
        [
            (get_pulse_bus_schedule(START_TIME_DEFAULT), "0", expected_program_str_0),
            (get_pulse_bus_schedule(START_TIME_NON_ZERO), "1", expected_program_str_1),
        ],
    )
    def test_generate_program(self, pulse_bus_schedule: PulseBusSchedule, name: str, expected_program_str: str):
        """Unit tests for _generate_program method"""

        sequencer_name = f"test_sequencer_program{name}"
        seq_idx = 0
        sequencer = SequencerQCM(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule)
        program = sequencer._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, nshots=1, repetition_duration=1000, num_bins=1
        )

        assert isinstance(program, Program)
        assert repr(dedent(repr(program))) == expected_program_str

    def test_execute(self, pulse_bus_schedule: PulseBusSchedule):
        """Unit tests for execute method"""

        qcm_qrn_name = "test_qcm_qrm_execute"
        cluster = Cluster(name="test_cluster_execute")
        qcm_qrm = QcmQrm(parent=cluster, name=qcm_qrn_name, slot_idx=0)
        sequencer = SequencerQCM(parent=qcm_qrm, name="sequencer_execute", seq_idx=0)

        with patch(
            "qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM._translate_pulse_bus_schedule"
        ) as mock_translate:
            with patch("qililab.drivers.instruments.qblox.sequencer_qcm.SequencerQCM.set") as mock_set:
                with patch(
                    "tests.unit.drivers.instruments.qblox.mock_utils.MockQcmQrm.arm_sequencer"
                ) as mock_arm_sequencer:
                    with patch(
                        "tests.unit.drivers.instruments.qblox.mock_utils.MockQcmQrm.start_sequencer"
                    ) as mock_start_sequencer:
                        sequencer.execute(
                            pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1
                        )
                        mock_set.assert_called_once()
                        mock_translate.assert_called_once()
                        mock_arm_sequencer.assert_called_once_with()
                        mock_start_sequencer.assert_called_once_with()
