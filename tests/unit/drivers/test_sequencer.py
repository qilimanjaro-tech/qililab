"""Tests for the Sequencer class."""
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest
from qcodes import Instrument
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyInstrument
from qpysequence.program import Program
from qpysequence.sequence import Sequence as QpySequence

from qililab.drivers.instruments.qblox.cluster import Cluster, QcmQrm
from qililab.drivers.instruments.qblox.sequencer import AWGSequencer
from qililab.drivers.interfaces.awg import AWG
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name
NUM_SLOTS = 20
START_TIME_DEFAULT = 0
START_TIME_NON_ZERO = 4


def get_pulse_bus_schedule(start_time):
    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=start_time)

    return PulseBusSchedule(timeline=[pulse_event], port=0)


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


class MockQcmQrm(DummyInstrument):
    def __init__(self, parent, name, slot_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {"test_submodule": MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False

    def arm_sequencer(self):
        return None

    def start_sequencer(self):
        return None


class MockCluster(DummyInstrument):
    def __init__(self, name, address=None, **kwargs):
        super().__init__(name)

        self.address = address
        self._num_slots = NUM_SLOTS
        self.submodules = {"test_submodule": MagicMock()}
        self._present_at_init = MagicMock()


class MockSequencer(DummyInstrument):
    def __init__(self, parent, name, seq_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self.seq_idx = seq_idx
        self._parent = parent
        self.add_parameter(
            "channel_map_path0_out0_en",
            label="Sequencer path 0 output 0 enable",
            docstring="Sets/gets sequencer channel map enable of path 0 to " "output 0.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        self.add_parameter(
            "channel_map_path1_out1_en",
            label="Sequencer path 1 output 1 enable",
            docstring="Sets/gets sequencer channel map enable of path 1 to " "output 1.",
            unit="",
            vals=vals.Bool(),
            set_parser=bool,
            get_parser=bool,
            set_cmd=None,
            get_cmd=None,
        )

        if parent.is_qcm_type:
            self.add_parameter(
                "channel_map_path0_out2_en",
                label="Sequencer path 0 output 2 enable.",
                docstring="Sets/gets sequencer channel map enable of path 0 " "to output 2.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )

            self.add_parameter(
                "channel_map_path1_out3_en",
                label="Sequencer path 1 output 3 enable.",
                docstring="Sets/gets sequencer channel map enable of path 1 " "to output 3.",
                unit="",
                vals=vals.Bool(),
                set_parser=bool,
                get_parser=bool,
                set_cmd=None,
                get_cmd=None,
            )


class TestSequencer:
    """Unit tests checking the Sequencer attributes and methods"""

    @classmethod
    def setup_class(cls):
        """Set up for all tests"""

        AWGSequencer.__bases__ = (MockSequencer, AWG)
        QcmQrm.__bases__ = (MockQcmQrm,)
        Cluster.__bases__ = (MockCluster,)

    @classmethod
    def teardown_class(cls):
        """Tear down after all tests have been run"""

        Instrument.close_all()

    def test_init(self):
        """Unit tests for init method"""

        sequencer_name = "test_sequencer_init"
        seq_idx = 0
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        assert sequencer._swap is False

    @patch("qililab.drivers.instruments.qblox.sequencer.AWGSequencer._map_outputs")
    @pytest.mark.parametrize("path0", [0, 1])
    def test_set_with_qililab_path(self, mock_map_outputs, path0):
        """Unit tests for set method with qililab path"""

        sequencer_name = "test_sequencer_set_qililab_path"
        seq_idx = 0
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequencer.set("path0", path0)
        mock_map_outputs.assert_called_once_with("path0", path0)

    @patch("tests.unit.drivers.test_sequencer.MockSequencer.set")
    def test_set_with_qblox_parameter(self, mock_super_set):
        """Unit tests for set method with qblox parameter"""

        sequencer_name = "test_sequencer_set_qblox_parameter"
        seq_idx = 0
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
 
        sequencer.set("channel_map_path0_out0_en", True)
        mock_super_set.assert_called_once_with("channel_map_path0_out0_en", True)

    @patch("tests.unit.drivers.test_sequencer.MockSequencer.set")
    @pytest.mark.parametrize("path0", [0, 1, 10])
    def test_map_outputs(self, mock_super_set, path0):
        """Unit tests for _map_outputs method"""

        sequencer_name = f"test_sequencer_map_outputs{path0}"
        seq_idx = 0
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        if path0 == 10:
            error_str = f"Impossible path configuration detected. path0 cannot be mapped to output {path0}."
            with pytest.raises(ValueError, match=error_str):
                sequencer._map_outputs("path0", path0)
                mock_super_set.assert_not_called()
                assert sequencer._swap is False

        else:
            sequencer._map_outputs("path0", path0)
            mock_super_set.assert_called_once_with("channel_map_path0_out0_en", True)
            if path0 == 0:
                assert sequencer._swap is False
            elif path0 == 1:
                assert sequencer._swap is True

    @pytest.mark.parametrize("path0", [0, 1])
    def test_generate_waveforms(self, pulse_bus_schedule, path0):
        """Unit tests for _generate_waveforms method"""

        sequencer_name = f"test_sequencer_waveforms{path0}"
        seq_idx = 0
        expected_waveforms_keys = [
            f"Gaussian(name=<{Gaussian.name}: 'gaussian'>, num_sigmas={PULSE_SIGMAS}) - {PULSE_DURATION}ns_I",
            f"Gaussian(name=<{Gaussian.name}: 'gaussian'>, num_sigmas={PULSE_SIGMAS}) - {PULSE_DURATION}ns_Q",
        ]
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

        sequencer.set("path0", path0)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule).to_dict()
        waveforms_keys = list(waveforms.keys())
        waveform_i = waveforms[waveforms_keys[0]]["data"]
        assert len(waveforms_keys) == len(expected_waveforms_keys)
        assert all(isinstance(waveforms[key], dict) for key in waveforms)
        assert all("data" in waveforms[key] for key in waveforms)
        assert all("index" in waveforms[key] for key in waveforms)
        assert all(isinstance(waveforms[key]["data"], list) for key in waveforms)
        if path0 % 2 != 0:
            assert len(set(waveform_i)) == 1
        else:
            assert len(set(waveform_i)) > 1

    @patch("qililab.drivers.instruments.qblox.sequencer.AWGSequencer._generate_waveforms")
    @patch("qililab.drivers.instruments.qblox.sequencer.AWGSequencer._generate_program")
    def test_translate_pulse_bus_schedule(self, mock_generate_program, mock_generate_waveforms, pulse_bus_schedule):
        """Unit tests for _translate_pulse_bus_schedule method"""

        sequencer_name = "test_sequencer_translate_pulse_bus_schedule"
        seq_idx = 0
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)

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
    def test_generate_program(self, pulse_bus_schedule, name, expected_program_str):
        """Unit tests for _generate_program method"""

        sequencer_name = f"test_sequencer_program{name}"
        seq_idx = 0
        sequencer = AWGSequencer(parent=MagicMock(), name=sequencer_name, seq_idx=seq_idx)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule)
        program = sequencer._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, nshots=1, repetition_duration=1000, num_bins=1
        )

        assert isinstance(program, Program)
        assert repr(dedent(repr(program))) == expected_program_str

    def test_execute(self, pulse_bus_schedule):
        """Unit tests for execute method"""

        qcm_qrn_name = "test_qcm_qrm_execute"
        cluster = Cluster(name="test_cluster_execute")
        qcm_qrm = QcmQrm(parent=cluster, name=qcm_qrn_name, slot_idx=0)
        sequencer = AWGSequencer(parent=qcm_qrm, name="sequencer_execute", seq_idx=0)

        with patch(
            "qililab.drivers.instruments.qblox.sequencer.AWGSequencer._translate_pulse_bus_schedule"
        ) as mock_translate:
            with patch("qililab.drivers.instruments.qblox.sequencer.AWGSequencer.set") as mock_set:
                with patch("tests.unit.drivers.test_sequencer.MockQcmQrm.arm_sequencer") as mock_arm_sequencer:
                    with patch("tests.unit.drivers.test_sequencer.MockQcmQrm.start_sequencer") as mock_start_sequencer:
                        sequencer.execute(
                            pulse_bus_schedule=pulse_bus_schedule, nshots=1, repetition_duration=1000, num_bins=1
                        )
                        mock_set.assert_called_once()
                        mock_translate.assert_called_once()
                        mock_arm_sequencer.assert_called_once()
                        mock_start_sequencer.assert_called_once()
