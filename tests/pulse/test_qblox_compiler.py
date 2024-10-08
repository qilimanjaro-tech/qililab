"""Tests for the Qblox Compiler class."""

import copy
import re
from unittest.mock import MagicMock

import numpy as np
import pytest
from qpysequence import Sequence
from qpysequence.utils.constants import AWG_MAX_GAIN

from qililab.instruments.qblox import QbloxQCM, QbloxQRM
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseSchedule, QbloxCompiler, Rectangular
from qililab.pulse.pulse_event import PulseEvent
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform():
    """platform fixture"""
    return build_platform(runcard=Galadriel.runcard)


class DummyQCM(QbloxQCM):
    """Dummy QCM class for testing"""

    _MIN_WAIT_TIME = 4

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.device = MagicMock()


class DummyQRM(QbloxQRM):
    """Dummy QRM class for testing"""

    _MIN_WAIT_TIME = 4

    def __init__(self, settings: dict):
        super().__init__(settings)
        self.device = MagicMock(autospec=True)


@pytest.fixture(name="qblox_compiler")
def fixture_qblox_compiler(platform: Platform):
    """Return an instance of Qblox Compiler class"""
    qcm_settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    qcm_settings.pop("name")
    dummy_qcm = DummyQCM(settings=qcm_settings)
    qrm_settings = copy.deepcopy(Galadriel.qblox_qrm_0)
    qrm_settings.pop("name")
    dummy_qrm = DummyQRM(settings=qrm_settings)
    platform.instruments.elements = [dummy_qcm, dummy_qrm]
    return QbloxCompiler(platform)


@pytest.fixture(name="qblox_compiler_2qrm")
def fixture_qblox_compiler_2qrm(platform: Platform):
    """Return an instance of Qblox Compiler class"""
    qcm_settings = copy.deepcopy(Galadriel.qblox_qcm_0)
    qcm_settings.pop("name")
    dummy_qcm = DummyQCM(settings=qcm_settings)
    qrm_0_settings = copy.deepcopy(Galadriel.qblox_qrm_0)
    qrm_0_settings.pop("name")
    qrm_1_settings = copy.deepcopy(Galadriel.qblox_qrm_1)
    qrm_1_settings.pop("name")
    platform.instruments.elements = [dummy_qcm, DummyQRM(settings=qrm_0_settings), DummyQRM(settings=qrm_1_settings)]
    return QbloxCompiler(platform)


@pytest.fixture(name="settings_6_sequencers")
def fixture_settings_6_sequencers():
    """settings for 6 sequencers"""
    sequencers = [
        {
            "identifier": seq_idx,
            "chip_port_id": "feedline_input",
            "qubit": 5 - seq_idx,
            "outputs": [0],
            "weights_i": [1, 1, 1, 1],
            "weights_q": [1, 1, 1, 1],
            "weighed_acq_enabled": False,
            "threshold": 0.5,
            "threshold_rotation": 30.0 * seq_idx,
            "num_bins": 1,
            "intermediate_frequency": 20000000,
            "gain_i": 0.001,
            "gain_q": 0.02,
            "gain_imbalance": 1,
            "phase_imbalance": 0,
            "offset_i": 0,
            "offset_q": 0,
            "hardware_modulation": True,
            "scope_acquire_trigger_mode": "sequencer",
            "scope_hardware_averaging": True,
            "sampling_rate": 1000000000,
            "integration_length": 8000,
            "integration_mode": "ssb",
            "sequence_timeout": 1,
            "acquisition_timeout": 1,
            "hardware_demodulation": True,
            "scope_store_enabled": True,
            "time_of_flight": 40,
        }
        for seq_idx in range(6)
    ]
    return {
        "alias": "test",
        "firmware": "0.4.0",
        "num_sequencers": 6,
        "out_offsets": [0.123, 1.23],
        "acquisition_delay_time": 100,
        "awg_sequencers": sequencers,
    }


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
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=1)
    return PulseBusSchedule(timeline=[pulse_event], port="feedline_input")


@pytest.fixture(name="pulse_bus_schedule_long_wait")
def fixture_pulse_bus_schedule_long_wait() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    pulse_event2 = PulseEvent(pulse=pulse, start_time=200_000, qubit=0)
    return PulseBusSchedule(timeline=[pulse_event, pulse_event2], port="feedline_input")


@pytest.fixture(name="pulse_bus_schedule_odd_qubits")
def fixture_pulse_bus_schedule_odd_qubits() -> PulseBusSchedule:
    """Returns a PulseBusSchedule with readout pulses for qubits 1, 3 and 5."""
    pulse = Pulse(amplitude=1.0, phase=0, duration=1000, frequency=7.0e9, pulse_shape=Rectangular())
    timeline = [PulseEvent(pulse=pulse, start_time=0, qubit=qubit) for qubit in [3, 1, 5]]
    return PulseBusSchedule(timeline=timeline, port="feedline_input")


@pytest.fixture(name="pulse_schedule_2qrm")
def fixture_pulse_schedule() -> PulseSchedule:
    """Return PulseBusSchedule instance."""
    pulse_event_0 = PulseEvent(
        pulse=Pulse(
            amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=Gaussian(num_sigmas=4)
        ),
        start_time=0,
        qubit=1,
    )
    pulse_event_1 = PulseEvent(
        pulse=Pulse(amplitude=0.8, phase=0.1, duration=50, frequency=1e9, pulse_shape=Rectangular()),
        start_time=12,
        qubit=2,
    )
    return PulseSchedule(
        [
            PulseBusSchedule(timeline=[pulse_event_0], port="feedline_input"),
            PulseBusSchedule(timeline=[pulse_event_1], port="feedline_output_2"),
        ]
    )


@pytest.fixture(name="long_pulse_bus_schedule")
def fixture_long_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=10**6, frequency=1e9, pulse_shape=Rectangular())
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    return PulseBusSchedule(timeline=[pulse_event], port="feedline_input")


@pytest.fixture(name="multiplexed_pulse_bus_schedule")
def fixture_multiplexed_pulse_bus_schedule() -> PulseBusSchedule:
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
                pulse_shape=Rectangular(),
            ),
            start_time=0,
            qubit=n,
        )
        for n in range(2)
    ]
    return PulseBusSchedule(timeline=timeline, port="feedline_input")


@pytest.fixture(name="pulse_schedule_odd_qubits")
def fixture_pulse_schedule_odd_qubits() -> PulseSchedule:
    """Returns a PulseBusSchedule with readout pulses for qubits 1, 3 and 5."""
    pulse = Pulse(amplitude=1.0, phase=0, duration=1000, frequency=7.0e9, pulse_shape=Rectangular())
    timeline = [PulseEvent(pulse=pulse, start_time=0, qubit=qubit) for qubit in [3, 1, 5]]
    return PulseSchedule([PulseBusSchedule(timeline=timeline, port="feedline_input")])


def are_q1asm_equal(a: str, b: str):
    """Compare two Q1ASM strings and parse them to remove spaces, new lines and long_wait counters"""
    return "".join([cmd for cmd in a.strip().split() if "long_wait" not in cmd]) == "".join(
        [cmd for cmd in b.strip().split() if "long_wait" not in cmd]
    )


class TestQbloxCompiler:
    """Unit tests checking the QbloxQCM attributes and methods"""

    def test_amplitude_and_phase_in_program(self, qblox_compiler, pulse_bus_schedule):
        """Test that the amplitude and the phase of a compiled pulse is added into the Qblox program."""

        amplitude = pulse_bus_schedule.timeline[0].pulse.amplitude
        phase = pulse_bus_schedule.timeline[0].pulse.phase
        pulse_bus_schedule_qcm = copy.copy(pulse_bus_schedule)
        pulse_bus_schedule_qcm.port = "drive_q0"

        pulse_schedule = PulseSchedule([pulse_bus_schedule_qcm, pulse_bus_schedule])

        sequences = qblox_compiler.compile(pulse_schedule, num_avg=1, repetition_duration=2000, num_bins=1)
        program = list(sequences.items())[1][1][0]._program

        expected_gain = int(amplitude * AWG_MAX_GAIN)
        expected_phase = int((phase % (2 * np.pi)) * 1e9 / (2 * np.pi))

        bin_loop = program.blocks[2].components[1]

        assert bin_loop.components[0].args[0] == expected_gain
        assert bin_loop.components[0].args[1] == expected_gain
        assert bin_loop.components[1].args[0] == expected_phase

    def test_qrm_compile(self, qblox_compiler, pulse_bus_schedule, pulse_bus_schedule2):
        """Test compile method."""
        pulse_schedule = PulseSchedule([pulse_bus_schedule])
        sequences = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "feedline_input_output_bus"
        ]
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert "Gaussian" in sequences[0]._waveforms._waveforms[0].name
        assert "Gaussian" in sequences[0]._waveforms._waveforms[1].name
        assert sum(sequences[0]._waveforms._waveforms[1].data) == 0
        assert len(sequences[0]._acquisitions._acquisitions) == 1
        assert sequences[0]._acquisitions._acquisitions[0].name == "acq_q0_0"
        assert sequences[0]._acquisitions._acquisitions[0].num_bins == 1
        assert sequences[0]._acquisitions._acquisitions[0].index == 0
        # test for different qubit, checkout that clearing the cache is working
        pulse_schedule2 = PulseSchedule([pulse_bus_schedule2])
        sequences = qblox_compiler.compile(pulse_schedule2, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "feedline_input_output_bus"
        ]
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert len(qblox_compiler.qblox_modules[1].cache.keys()) == 1

    def test_compile_multiplexing(self, qblox_compiler, multiplexed_pulse_bus_schedule: PulseBusSchedule):
        """Test compile method with a multiplexed pulse bus schedule."""
        multiplexed_pulse_schedule = PulseSchedule([multiplexed_pulse_bus_schedule])
        sequences = qblox_compiler.compile(
            multiplexed_pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1
        )["feedline_input_output_bus"]
        assert isinstance(sequences, list)
        assert len(sequences) == 2
        assert all(isinstance(sequence, Sequence) for sequence in sequences)

        # test cache
        single_freq_schedules = multiplexed_pulse_bus_schedule.qubit_schedules()
        qrm = qblox_compiler.qblox_modules[1]
        assert len(qrm.cache) == len(single_freq_schedules)
        assert all(
            cache_schedule == expected_schedule
            for cache_schedule, expected_schedule in zip(qrm.cache.values(), single_freq_schedules)
        )

    def test_qrm_compile_2qrm(
        self,
        qblox_compiler_2qrm: QbloxCompiler,
        pulse_bus_schedule: PulseBusSchedule,
        pulse_schedule_2qrm: PulseSchedule,
    ):
        """Test compile method for 2 qrms. First check a pulse schedule with 2 qrms, then one with
        only 1 qrm. Check that compiling the second sequence erases unused sequences in the unused qrm cache."""
        program = qblox_compiler_2qrm.compile(pulse_schedule_2qrm, num_avg=1000, repetition_duration=2000, num_bins=1)

        assert len(program.items()) == 2
        assert "feedline_input_output_bus" in program
        assert "feedline_input_output_bus_2" in program
        assert len(qblox_compiler_2qrm.qblox_modules[1].cache.keys()) == 1
        assert len(qblox_compiler_2qrm.qblox_modules[2].cache.keys()) == 1

        assert list(qblox_compiler_2qrm.qblox_modules[1].sequences.keys()) == [1]
        assert list(qblox_compiler_2qrm.qblox_modules[2].sequences.keys()) == [0]

        assert len(program["feedline_input_output_bus"]) == 1
        assert len(program["feedline_input_output_bus_2"]) == 1

        sequences_0 = program["feedline_input_output_bus"][0]
        sequences_1 = program["feedline_input_output_bus_2"][0]

        assert isinstance(sequences_0, Sequence)
        assert isinstance(sequences_1, Sequence)

        assert "Gaussian" in sequences_0._waveforms._waveforms[0].name
        assert "Rectangular" in sequences_1._waveforms._waveforms[0].name

        q1asm_0 = """
            setup:
                            move             0, R0
                            move             1, R1
                            move             1000, R2
                            wait_sync        4

            start:
                            reset_ph
                            set_mrk          0
                            upd_param        4

            average:
                            move             0, R3
            bin:
                            set_awg_gain     26213, 26213
                            set_ph           191690305
                            play             0, 1, 4
                            wait             220
                            acquire          0, R3, 4
            long_wait_1:
                            wait             1772

                            add              R3, 1, R3
                            nop
                            jlt              R3, 1, @bin
                            loop             R2, @average
            stop:
                            set_mrk          0
                            upd_param        4
                            stop
        """

        q1asm_1 = """
            setup:
                            move             0, R0
                            move             1, R1
                            move             1000, R2
                            wait_sync        4

            start:
                            reset_ph
                            set_mrk          0
                            upd_param        4

            average:
                            move             0, R3
            bin:
            long_wait_2:
                            wait             12

                            set_awg_gain     26213, 26213
                            set_ph           15915494
                            play             0, 1, 4
                            wait             220
                            acquire_weighed  0, R3, R0, R1, 4
            long_wait_3:
                            wait             1760

                            add              R3, 1, R3
                            nop
                            jlt              R3, 1, @bin
                            loop             R2, @average
            stop:
                            set_mrk          0
                            upd_param        4
                            stop
        """
        seq_0_q1asm = sequences_0._program
        seq_1_q1asm = sequences_1._program

        assert are_q1asm_equal(q1asm_0, repr(seq_0_q1asm))
        assert are_q1asm_equal(q1asm_1, repr(seq_1_q1asm))

        # qblox modules 1 is the first qrm and 2 is the second
        assert qblox_compiler_2qrm.qblox_modules[1].cache == {1: pulse_schedule_2qrm.elements[0]}
        assert qblox_compiler_2qrm.qblox_modules[2].cache == {0: pulse_schedule_2qrm.elements[1]}
        assert qblox_compiler_2qrm.qblox_modules[1].sequences == {1: sequences_0}
        assert qblox_compiler_2qrm.qblox_modules[2].sequences == {0: sequences_1}

        # check that the qcm is empty since we didnt send anything to it
        assert not qblox_compiler_2qrm.qblox_modules[0].cache
        assert not qblox_compiler_2qrm.qblox_modules[0].sequences

        # compile next sequence
        # test for different qubit, checkout that clearing the cache is working
        pulse_schedule2 = PulseSchedule([pulse_bus_schedule])
        program = qblox_compiler_2qrm.compile(pulse_schedule2, num_avg=1000, repetition_duration=2000, num_bins=1)

        assert len(program.items()) == 1
        assert "feedline_input_output_bus" in program
        assert len(qblox_compiler_2qrm.qblox_modules[1].cache.keys()) == 1
        assert list(qblox_compiler_2qrm.qblox_modules[1].sequences.keys()) == [0]
        assert len(program["feedline_input_output_bus"]) == 1

        sequences_0 = program["feedline_input_output_bus"][0]
        assert isinstance(sequences_0, Sequence)

        assert "Gaussian" in sequences_0._waveforms._waveforms[0].name
        # qblox modules 1 is the first qrm and 2 is the second
        assert qblox_compiler_2qrm.qblox_modules[1].cache == {0: pulse_bus_schedule}
        assert qblox_compiler_2qrm.qblox_modules[1].sequences == {0: sequences_0}

        assert not qblox_compiler_2qrm.qblox_modules[0].cache
        assert not qblox_compiler_2qrm.qblox_modules[0].sequences
        assert not qblox_compiler_2qrm.qblox_modules[2].cache
        assert not qblox_compiler_2qrm.qblox_modules[2].sequences

        q1asm_0 = """
            setup:
                            move             0, R0
                            move             1, R1
                            move             1000, R2
                            wait_sync        4

            start:
                            reset_ph
                            set_mrk          0
                            upd_param        4

            average:
                            move             0, R3
            bin:
                            set_awg_gain     26213, 26213
                            set_ph           191690305
                            play             0, 1, 4
                            wait             220
                            acquire_weighed  0, R3, R0, R1, 4
            long_wait_4:
                            wait             1772

                            add              R3, 1, R3
                            nop
                            jlt              R3, 1, @bin
                            loop             R2, @average
            stop:
                            set_mrk          0
                            upd_param        4
                            stop
        """
        sequences_0_program = sequences_0._program
        assert are_q1asm_equal(q1asm_0, repr(sequences_0_program))

    def test_long_wait_between_pulses(
        self, pulse_bus_schedule_long_wait: PulseBusSchedule, qblox_compiler: QbloxCompiler
    ):
        """test that a long wait is added properly between pulses if the wait time is longer than the max wait allowed by qblox"""
        pulse_schedule = PulseSchedule([pulse_bus_schedule_long_wait])
        program = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=400_000, num_bins=1)
        q1asm = """
        setup:
                        move             0, R0
                        move             1, R1
                        move             1000, R2
                        wait_sync        4

        start:
                        reset_ph
                        set_mrk          0
                        upd_param        4

        average:
                        move             0, R3
        bin:
                        set_awg_gain     26213, 26213
                        set_ph           191690305
                        play             0, 1, 4
                        wait             220
                        acquire_weighed  0, R3, R0, R1, 4
        long_wait_1:
                        move             3, R4
        long_wait_1_loop:
                        wait             65532
                        loop             R4, @long_wait_1_loop
                        wait             3396

                        set_awg_gain     26213, 26213
                        set_ph           191690305
                        play             0, 1, 4
                        wait             220
                        acquire_weighed  1, R3, R0, R1, 4
        long_wait_2:
                        move             3, R5
        long_wait_2_loop:
                        wait             65532
                        loop             R5, @long_wait_2_loop
                        wait             2956

                        add              R3, 1, R3
                        nop
                        jlt              R3, 1, @bin
                        loop             R2, @average
        stop:
                        set_mrk          0
                        upd_param        4
                        stop
        """

        sequences_program = program["feedline_input_output_bus"][0]._program
        assert are_q1asm_equal(q1asm, repr(sequences_program))

    def test_qubit_to_sequencer_mapping(
        self, qblox_compiler: QbloxCompiler, pulse_schedule_odd_qubits: PulseSchedule, settings_6_sequencers: dict
    ):
        """Test that the pulses to odd qubits are mapped to odd sequencers."""
        qblox_compiler.qblox_modules[1] = DummyQRM(settings=settings_6_sequencers)  # change qrm from fixture

        qblox_compiler.compile(
            pulse_schedule=pulse_schedule_odd_qubits, num_avg=1, repetition_duration=5000, num_bins=1
        )
        assert list(qblox_compiler.qblox_modules[1].cache.keys()) == [0, 2, 4]

    def test_acquisition_data_is_removed_when_calling_compile_twice(
        self, qblox_compiler, pulse_bus_schedule
    ):  # FIXME: acquisition data should be removed at acquisition and not at compilation
        """Test that the acquisition data of the QRM device is deleted when calling compile twice."""
        pulse_event = PulseSchedule([pulse_bus_schedule])
        sequences = qblox_compiler.compile(pulse_event, num_avg=1000, repetition_duration=100, num_bins=1)[
            "feedline_input_output_bus"
        ]
        qblox_compiler.qblox_modules[1].sequences = {
            0: sequences[0]
        }  # do this manually since we're not calling the upload method
        sequences2 = qblox_compiler.compile(pulse_event, num_avg=1000, repetition_duration=100, num_bins=1)[
            "feedline_input_output_bus"
        ]
        assert len(sequences) == 1
        assert len(sequences2) == 1
        assert sequences[0] is sequences2[0]
        qblox_compiler.qblox_modules[1].device.delete_acquisition_data.assert_called_once_with(sequencer=0, all=True)

    def test_error_program_gt_repetition_duration(
        self, long_pulse_bus_schedule: PulseBusSchedule, qblox_compiler: QbloxCompiler
    ):
        """test that error is raised if circuit execution duration is longer than repetition duration"""
        pulse_schedule = PulseSchedule([long_pulse_bus_schedule])
        repetition_duration = 2000
        error_string = f"Circuit execution time cannnot be longer than repetition duration but found circuit time {long_pulse_bus_schedule.duration} > {repetition_duration} for qubit 0"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            qblox_compiler.compile(pulse_schedule=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)

    def test_no_qrm_raises_error(self, platform: Platform):
        """test that error is raised if no qrm is found in platform"""
        qcm_settings = copy.deepcopy(Galadriel.qblox_qcm_0)
        qcm_settings.pop("name")
        dummy_qcm = DummyQCM(settings=qcm_settings)
        platform.instruments.elements = [dummy_qcm]
        error_string = "No QRM modules found in platform instruments"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            QbloxCompiler(platform)
