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


@pytest.fixture(name="settings_6_sequencers")
def fixture_settings_6_sequencers():
    """settings for 6 sequencers"""
    sequencers = [
        {
            "identifier": seq_idx,
            "chip_port_id": "feedline_input",
            "qubit": 5 - seq_idx,
            "output_i": 1,
            "output_q": 0,
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
        program = list(sequences.items())[1][1][0]._program  # pylint: disable=protected-access

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

    def test_compile_swaps_the_i_and_q_channels_when_mapping_is_not_supported_in_hw(self, qblox_compiler):
        """Test that the compile method swaps the I and Q channels when the output mapping is not supported in HW."""
        # We change the dictionary and initialize the QCM
        qrm = qblox_compiler.qblox_modules[1]
        qrm_settings = qrm.to_dict()
        qrm_settings.pop("name")
        qrm.settings.awg_sequencers[0].path_i = 1
        qrm.settings.awg_sequencers[0].path_q = 0
        qrm.settings.awg_sequencers[0].weights_i = [1, 2, 3]
        qrm.settings.awg_sequencers[0].weights_q = [4, 5, 6]
        # We create a pulse bus schedule
        pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=Gaussian(num_sigmas=4))
        pulse_schedule = PulseSchedule(
            [PulseBusSchedule(timeline=[PulseEvent(pulse=pulse, start_time=0, qubit=0)], port="feedline_input")]
        )
        sequences = qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)[
            "feedline_input_output_bus"
        ]
        # We assert that the waveform/weights of the first path is all zeros and the waveform of the second path is the gaussian
        waveforms = sequences[0]._waveforms._waveforms  # pylint: disable=protected-access
        assert np.allclose(waveforms[0].data, 0)
        assert np.allclose(waveforms[1].data, pulse.envelope(amplitude=1))
        weights = sequences[0]._weights.to_dict()  # pylint: disable=protected-access
        assert np.allclose(weights["pair_0_I"]["data"], [4, 5, 6])
        assert np.allclose(weights["pair_0_Q"]["data"], [1, 2, 3])

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
        qblox_compiler.qblox_modules[1].device.delete_acquisition_data.assert_called_once_with(
            sequencer=0, name="default"
        )

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

    def test_target_more_than_one_readout_port_raises_error(self, qblox_compiler, pulse_bus_schedule):
        """Test compile method."""
        pulse_schedule = PulseSchedule([pulse_bus_schedule, pulse_bus_schedule])
        error_string = "readout pulses targeted at more than one port. Expected only one target port and instead got 2"
        with pytest.raises(ValueError, match=re.escape(error_string)):
            qblox_compiler.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)