"""Tests for the Sequencer class."""
from textwrap import dedent
from unittest.mock import MagicMock

import pytest
from qcodes import validators as vals
from qcodes.tests.instrument_mocks import DummyInstrument
from qpysequence.program import Program

from qililab.drivers.instruments.qblox.sequencer import AWGSequencer
from qililab.drivers.interfaces.awg import AWG
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from qililab.typings import PulseShapeName

PULSE_SIGMAS = 4
PULSE_AMPLITUDE = 1
PULSE_PHASE = 0
PULSE_DURATION = 50
PULSE_FREQUENCY = 1e9
PULSE_NAME = Gaussian.name


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=PULSE_SIGMAS)
    pulse = Pulse(
        amplitude=PULSE_AMPLITUDE,
        phase=PULSE_PHASE,
        duration=PULSE_DURATION,
        frequency=PULSE_FREQUENCY,
        pulse_shape=pulse_shape,
    )
    pulse_event = PulseEvent(pulse=pulse, start_time=0)
    return PulseBusSchedule(timeline=[pulse_event], port=0)


class MockCluster(DummyInstrument):
    def __init__(self, name, address=None, **kwargs):
        super().__init__(name, **kwargs)

        self.address = address
        self.submodules = {"test_submodule": MagicMock()}


class MockQcmQrm(DummyInstrument):
    def __init__(self, name, slot_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self._slot_idx = slot_idx
        self.submodules = {"test_submodule": MagicMock()}
        self.is_qcm_type = True
        self.is_qrm_type = False
        self.is_rf_type = False


class MockSequencer(DummyInstrument):
    def __init__(self, parent, name, seq_idx, **kwargs):
        super().__init__(name, **kwargs)

        # Store sequencer index
        self.seq_idx = seq_idx

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

    def test_init(self):
        AWGSequencer.__bases__ = (MockSequencer, AWG)
        sequencer_name = "test_sequencer_init"
        seq_idx = 0

        qcm_qrm = MockQcmQrm(name="test_qcm_qrm_init", slot_idx=0)
        sequencer = AWGSequencer(parent=qcm_qrm, name=sequencer_name, seq_idx=seq_idx)

        assert sequencer.get_swap_state() is False

    def test_generate_waveforms(self, pulse_bus_schedule):
        AWGSequencer.__bases__ = (MockSequencer, AWG)
        sequencer_name = "test_sequencer_waveforms"
        seq_idx = 0
        expected_waveforms_keys = [
            f"Gaussian(name=<{Gaussian.name}: 'gaussian'>, num_sigmas={PULSE_SIGMAS}) - {PULSE_DURATION}ns_I",
            f"Gaussian(name=<{Gaussian.name}: 'gaussian'>, num_sigmas={PULSE_SIGMAS}) - {PULSE_DURATION}ns_Q",
        ]
        qcm_qrm = MockQcmQrm(name="test_qcm_qrm_waveforms", slot_idx=0)
        sequencer = AWGSequencer(parent=qcm_qrm, name=sequencer_name, seq_idx=seq_idx)

        waveforms = sequencer._generate_waveforms(pulse_bus_schedule).to_dict()
        waveforms_keys = list(waveforms.keys())
        assert len(waveforms_keys) == len(expected_waveforms_keys)
        assert waveforms_keys == expected_waveforms_keys

    def test_generate_program(self, pulse_bus_schedule):
        AWGSequencer.__bases__ = (MockSequencer, AWG)
        sequencer_name = "test_sequencer_program"
        seq_idx = 0
        qcm_qrm = MockQcmQrm(name="test_qcm_qrm_program", slot_idx=0)
        sequencer = AWGSequencer(parent=qcm_qrm, name=sequencer_name, seq_idx=seq_idx)
        expected_program_str = "setup:\n    move             1, R0\n    wait_sync        4\n\naverage:\n    move             0, R1\n    bin:\n        reset_ph\n        set_awg_gain     32767, 32767\n        set_ph           0\n        play             0, 1, 4\n        long_wait_1:\n            wait             996\n\n        add              R1, 1, R1\n        nop\n        jlt              R1, 1, @bin\n    loop             R0, @average\nstop:\n    stop\n\n"
        expected_program_str = repr(expected_program_str)
        waveforms = sequencer._generate_waveforms(pulse_bus_schedule)
        program = sequencer._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, nshots=1, repetition_duration=1000, num_bins=1
        )

        assert isinstance(program, Program)
        assert repr(dedent(repr(program))) == expected_program_str
