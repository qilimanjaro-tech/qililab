"""Tests for the Qblox Compiler class."""

import copy
import re
from unittest.mock import MagicMock

import numpy as np
import pytest
from qpysequence import Sequence
from qpysequence.constants import AWG_MAX_GAIN

from qililab.instruments.qblox import QbloxQCM, QbloxQRM
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseSchedule, QbloxCompiler, Rectangular
from qililab.pulse.pulse_event import PulseEvent
from qililab.settings.digital.digital_compilation_bus_settings import DigitalCompilationBusSettings
from qililab.typings import AcquireTriggerMode, IntegrationMode, Parameter
from qililab.typings.enums import Line


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

@pytest.fixture(name="qcm_0")
def fixture_qcm_0():
    settings = {
        "alias": "qcm_0",
        "out_offsets": [0, 0.5, 0.7, 0.8],
        "awg_sequencers": [
            {
                "identifier": 0,
                "outputs": [0, 1],
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
            },
            {
                "identifier": 1,
                "outputs": [0, 1],
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
            },
        ],
    }
    return DummyQCM(settings=settings)

@pytest.fixture(name="qrm_0")
def fixture_qrm_0():
    settings = {
        "alias": "qrm_0",
        "out_offsets": [0.123, 1.23],
        "awg_sequencers": [
            {
                "identifier": 0,
                "outputs": [0, 1],
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_123,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: True,
                Parameter.TIME_OF_FLIGHT.value: 40,
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
            {
                "identifier": 1,
                "outputs": [0, 1],
                Parameter.IF.value: 200_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_000,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: False,
                Parameter.TIME_OF_FLIGHT.value: 40,
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
            {
                "identifier": 2,
                "outputs": [0, 1],
                Parameter.IF.value: 200_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_000,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: False,
                Parameter.TIME_OF_FLIGHT.value: 40,
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            },
        ],
    }
    return DummyQRM(settings=settings)

@pytest.fixture(name="qrm_1")
def fixture_qrm_1():
    settings = {
        "alias": "qrm_1",
        "out_offsets": [0.123, 1.23],
        "awg_sequencers": [
            {
                "identifier": 0,
                "outputs": [0, 1],
                Parameter.IF.value: 100_000_000,
                Parameter.GAIN_I.value: 1,
                Parameter.GAIN_Q.value: 1,
                Parameter.GAIN_IMBALANCE.value: 0,
                Parameter.PHASE_IMBALANCE.value: 0,
                Parameter.OFFSET_I.value: 0,
                Parameter.OFFSET_Q.value: 0,
                Parameter.HARDWARE_MODULATION.value: False,
                Parameter.SCOPE_ACQUIRE_TRIGGER_MODE.value: AcquireTriggerMode.SEQUENCER.value,
                Parameter.SCOPE_HARDWARE_AVERAGING.value: True,
                Parameter.SAMPLING_RATE.value: 1.0e09,
                Parameter.INTEGRATION_LENGTH.value: 2_123,
                Parameter.INTEGRATION_MODE.value: IntegrationMode.SSB.value,
                Parameter.SEQUENCE_TIMEOUT.value: 1,
                Parameter.ACQUISITION_TIMEOUT.value: 1,
                Parameter.HARDWARE_DEMODULATION.value: True,
                Parameter.SCOPE_STORE_ENABLED.value: True,
                Parameter.TIME_OF_FLIGHT.value: 40,
                Parameter.THRESHOLD.value: 0.5,
                Parameter.THRESHOLD_ROTATION.value: 45.0,
            }
        ],
    }
    return DummyQRM(settings=settings)

@pytest.fixture(name="buses")
def fixture_buses() -> dict[str, DigitalCompilationBusSettings]:
    return {
        "drive_q0": DigitalCompilationBusSettings(
            line=Line.DRIVE,
            qubits=[0]
        ),
        "flux_q0": DigitalCompilationBusSettings(
            line=Line.FLUX,
            qubits=[0]
        ),
        "readout_q0": DigitalCompilationBusSettings(
            line=Line.READOUT,
            qubits=[0],
        ),
        "readout_q1": DigitalCompilationBusSettings(
            line=Line.READOUT,
            qubits=[1],
        ),
        "readout_q2": DigitalCompilationBusSettings(
            line=Line.READOUT,
            qubits=[2],
        ),
        "readout_q3": DigitalCompilationBusSettings(
            line=Line.READOUT,
            qubits=[3],
        ),
    }

@pytest.fixture(name="bus_to_module_and_sequencer_mapping")
def fixture_bus_to_module_and_sequencer_mapping(qcm_0: DummyQCM, qrm_0: DummyQRM, qrm_1: DummyQRM):
    return {
        "drive_q0": {
            "module": qcm_0,
            "sequencer": qcm_0.get_sequencer(0)
        },
        "flux_q0": {
            "module": qcm_0,
            "sequencer": qcm_0.get_sequencer(1)
        },
        "readout_q0": {
            "module": qrm_0,
            "sequencer": qrm_0.get_sequencer(0)
        },
        "readout_q1": {
            "module": qrm_0,
            "sequencer": qrm_0.get_sequencer(1)
        },
        "readout_q2": {
            "module": qrm_0,
            "sequencer": qrm_0.get_sequencer(2)
        },
        "readout_q3": {
            "module": qrm_1,
            "sequencer": qrm_1.get_sequencer(0)
        }
    }


@pytest.fixture(name="qblox_compiler")
def fixture_qblox_compiler(buses, bus_to_module_and_sequencer_mapping):
    """Return an instance of Qblox Compiler class"""
    return QbloxCompiler(buses, bus_to_module_and_sequencer_mapping)


@pytest.fixture(name="pulse_bus_schedule")
def fixture_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    return PulseBusSchedule(timeline=[pulse_event], bus_alias="readout_q0")


@pytest.fixture(name="pulse_bus_schedule2")
def fixture_pulse_bus_schedule2() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=1)
    return PulseBusSchedule(timeline=[pulse_event], bus_alias="readout_q1")


@pytest.fixture(name="pulse_bus_schedule_long_wait")
def fixture_pulse_bus_schedule_long_wait() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    pulse_event2 = PulseEvent(pulse=pulse, start_time=200_000, qubit=0)
    return PulseBusSchedule(timeline=[pulse_event, pulse_event2], bus_alias="readout_q0")


@pytest.fixture(name="pulse_schedule_2qrm")
def fixture_pulse_schedule() -> PulseSchedule:
    """Return PulseBusSchedule instance."""
    pulse_event_0 = PulseEvent(
        pulse=Pulse(
            amplitude=0.8, phase=np.pi / 2 + 12.2, duration=50, frequency=1e9, pulse_shape=Gaussian(num_sigmas=4)
        ),
        start_time=0,
        qubit=2,
    )
    pulse_event_1 = PulseEvent(
        pulse=Pulse(amplitude=0.8, phase=0.1, duration=50, frequency=1e9, pulse_shape=Rectangular()),
        start_time=12,
        qubit=3,
    )
    return PulseSchedule(
        [
            PulseBusSchedule(timeline=[pulse_event_0], bus_alias="readout_q2"),
            PulseBusSchedule(timeline=[pulse_event_1], bus_alias="readout_q3"),
        ]
    )


@pytest.fixture(name="long_pulse_bus_schedule")
def fixture_long_pulse_bus_schedule() -> PulseBusSchedule:
    """Return PulseBusSchedule instance."""
    pulse = Pulse(amplitude=0.8, phase=np.pi / 2 + 12.2, duration=10**6, frequency=1e9, pulse_shape=Rectangular())
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    return PulseBusSchedule(timeline=[pulse_event], bus_alias="readout_q0")


# @pytest.fixture(name="pulse_schedule_odd_qubits")
# def fixture_pulse_schedule_odd_qubits() -> PulseSchedule:
#     """Returns a PulseBusSchedule with readout pulses for qubits 1, 3 and 5."""
#     pulse = Pulse(amplitude=1.0, phase=0, duration=1000, frequency=7.0e9, pulse_shape=Rectangular())
#     timeline = [PulseEvent(pulse=pulse, start_time=0, qubit=qubit) for qubit in [3, 1, 5]]
#     return PulseSchedule([PulseBusSchedule(timeline=timeline, port="feedline_input")])


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
        pulse_bus_schedule_qcm.bus_alias = "drive_q0"

        pulse_schedule = PulseSchedule([pulse_bus_schedule_qcm, pulse_bus_schedule])

        sequences = qblox_compiler.compile(pulse_schedule, num_avg=1, repetition_duration=2000, num_bins=1)
        program = list(sequences.items())[1][1][0]._program

        expected_gain = int(amplitude * AWG_MAX_GAIN)
        expected_phase = int((phase % (2 * np.pi)) * 1e9 / (2 * np.pi))

        bin_loop = program.blocks[3].components[1]

        assert bin_loop.components[0].args[0] == expected_gain
        assert bin_loop.components[0].args[1] == expected_gain
        assert bin_loop.components[1].args[0] == expected_phase

    def test_qrm_compile(self, qblox_compiler: QbloxCompiler, pulse_bus_schedule, pulse_bus_schedule2):
        """Test compile method."""
        pulse_schedule = PulseSchedule([pulse_bus_schedule])
        sequences = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "readout_q0"
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
            "readout_q1"
        ]
        assert isinstance(sequences, list)
        assert len(sequences) == 1
        assert isinstance(sequences[0], Sequence)
        assert len(qblox_compiler.module_and_sequencer_per_bus["readout_q1"]["module"].cache.keys()) == 2

    def test_qrm_compile_2qrm(
        self,
        qblox_compiler: QbloxCompiler,
        pulse_schedule_2qrm: PulseSchedule,
    ):
        """Test compile method for 2 qrms. First check a pulse schedule with 2 qrms, then one with
        only 1 qrm. Check that compiling the second sequence erases unused sequences in the unused qrm cache."""
        program = qblox_compiler.compile(pulse_schedule_2qrm, num_avg=1000, repetition_duration=2000, num_bins=1)

        assert len(program.items()) == 2
        assert "readout_q2" in program
        assert "readout_q3" in program
        assert len(qblox_compiler.module_and_sequencer_per_bus["readout_q2"]["module"].cache.keys()) == 1
        assert len(qblox_compiler.module_and_sequencer_per_bus["readout_q3"]["module"].cache.keys()) == 1

        assert list(qblox_compiler.module_and_sequencer_per_bus["readout_q2"]["module"].sequences.keys()) == [2]
        assert list(qblox_compiler.module_and_sequencer_per_bus["readout_q3"]["module"].sequences.keys()) == [0]

        assert len(program["readout_q2"]) == 1
        assert len(program["readout_q3"]) == 1

        sequences_0 = program["readout_q2"][0]
        sequences_1 = program["readout_q3"][0]

        assert isinstance(sequences_0, Sequence)
        assert isinstance(sequences_1, Sequence)

        assert "Gaussian" in sequences_0._waveforms._waveforms[0].name
        assert "Rectangular" in sequences_1._waveforms._waveforms[0].name

        q1asm_0 = """
            setup:
                            move             0, R0
                            move             1, R1
                            wait_sync        4

            start:
                            reset_ph
                            set_mrk          0
                            upd_param        4

                            move             1000, R2

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
                            wait_sync        4

            start:
                            reset_ph
                            set_mrk          0
                            upd_param        4

                            move             1000, R2

            average:
                            move             0, R3
            bin:
            long_wait_2:
                            wait             12

                            set_awg_gain     26213, 26213
                            set_ph           15915494
                            play             0, 1, 4
                            wait             220
                            acquire          0, R3, 4
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
        seq_0_q1asm = repr(sequences_0._program)
        seq_1_q1asm = repr(sequences_1._program)

        assert are_q1asm_equal(q1asm_0, seq_0_q1asm)
        assert are_q1asm_equal(q1asm_1, seq_1_q1asm)

        # qblox modules 1 is the first qrm and 2 is the second
        assert qblox_compiler.module_and_sequencer_per_bus["readout_q2"]["module"].cache == {2: pulse_schedule_2qrm.elements[0]}
        assert qblox_compiler.module_and_sequencer_per_bus["readout_q3"]["module"].cache == {0: pulse_schedule_2qrm.elements[1]}
        assert qblox_compiler.module_and_sequencer_per_bus["readout_q2"]["module"].sequences == {2: sequences_0}
        assert qblox_compiler.module_and_sequencer_per_bus["readout_q3"]["module"].sequences == {0: sequences_1}

        # check that the qcm is empty since we didnt send anything to it
        assert not qblox_compiler.module_and_sequencer_per_bus["drive_q0"]["module"].cache
        assert not qblox_compiler.module_and_sequencer_per_bus["drive_q0"]["module"].sequences

    def test_long_wait_between_pulses(
        self, pulse_bus_schedule_long_wait: PulseBusSchedule, qblox_compiler: QbloxCompiler
    ):
        """test that a long wait is added properly between pulses if the wait time is longer than the max wait allowed by qblox"""
        expected_q1asm = """
        setup:
                        move             0, R0
                        move             1, R1
                        wait_sync        4

        start:
                        reset_ph
                        set_mrk          0
                        upd_param        4

                        move             1000, R2

        average:
                        move             0, R3
        bin:
                        set_awg_gain     26213, 26213
                        set_ph           191690305
                        play             0, 1, 4
                        wait             220
                        acquire          0, R3, 4
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
                        acquire          1, R3, 4
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

        pulse_schedule = PulseSchedule([pulse_bus_schedule_long_wait])
        program = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=400_000, num_bins=1)
        q1asm = repr(program["readout_q0"][0]._program)

        assert are_q1asm_equal(q1asm, expected_q1asm)

    # def test_qubit_to_sequencer_mapping(
    #     self, qblox_compiler: QbloxCompiler, pulse_schedule_odd_qubits: PulseSchedule, settings_6_sequencers: dict
    # ):
    #     """Test that the pulses to odd qubits are mapped to odd sequencers."""
    #     qblox_compiler.qblox_modules[1] = DummyQRM(settings=settings_6_sequencers)  # change qrm from fixture

    #     qblox_compiler.compile(
    #         pulse_schedule=pulse_schedule_odd_qubits, num_avg=1, repetition_duration=5000, num_bins=1
    #     )
    #     assert list(qblox_compiler.qblox_modules[1].cache.keys()) == [0, 2, 4]

    def test_acquisition_data_is_removed_when_calling_compile_twice(
        self, qblox_compiler: QbloxCompiler, pulse_bus_schedule
    ):  # FIXME: acquisition data should be removed at acquisition and not at compilation
        """Test that the acquisition data of the QRM device is deleted when calling compile twice."""
        pulse_event = PulseSchedule([pulse_bus_schedule])
        sequences = qblox_compiler.compile(pulse_event, num_avg=1000, repetition_duration=100, num_bins=1)[
            "readout_q0"
        ]
        qblox_compiler.module_and_sequencer_per_bus["readout_q0"]["module"].sequences = {
            0: sequences[0]
        }  # do this manually since we're not calling the upload method
        sequences2 = qblox_compiler.compile(pulse_event, num_avg=1000, repetition_duration=100, num_bins=1)[
            "readout_q0"
        ]
        assert len(sequences) == 1
        assert len(sequences2) == 1
        assert sequences[0] is sequences2[0]
        qblox_compiler.module_and_sequencer_per_bus["readout_q0"]["module"].device.delete_acquisition_data.assert_called_once_with(sequencer=0, all=True)

    def test_error_program_gt_repetition_duration(
        self, long_pulse_bus_schedule: PulseBusSchedule, qblox_compiler: QbloxCompiler
    ):
        """test that error is raised if circuit execution duration is longer than repetition duration"""
        pulse_schedule = PulseSchedule([long_pulse_bus_schedule])
        repetition_duration = 2000
        error_string = f"Circuit execution time cannnot be longer than repetition duration but found circuit time {long_pulse_bus_schedule.duration} > {repetition_duration} for qubit 0"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            qblox_compiler.compile(pulse_schedule=pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)
