"""Qblox module class"""
import itertools
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple, cast

import numpy as np
from qpysequence.acquisitions import Acquisitions
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Program, Register
from qpysequence.program.instructions import Play, ResetPh, Stop, Wait
from qpysequence.sequence import Sequence as QpySequence
from qpysequence.waveforms import Waveforms
from qpysequence.weights import Weights

from qililab.config import logger
from qililab.instruments.awg import AWG
from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer
from qililab.instruments.awg_settings.awg_sequencer_path import AWGSequencerPathIdentifier
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.pulse import PulseBusSchedule, PulseShape
from qililab.typings.enums import Parameter
from qililab.typings.instruments import Pulsar, QcmQrm


class QbloxModule(AWG):
    """Qblox Module class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    _MAX_BINS: int = 131072
    _NUM_MAX_SEQUENCERS: int = 6
    _NUM_MAX_AWG_OUT_CHANNELS: int = 4
    _NUM_MAX_AWG_IQ_CHANNELS = int(_NUM_MAX_AWG_OUT_CHANNELS / 2)
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxModuleSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            awg_sequencers (Sequence[AWGQbloxSequencer]): list of settings for each sequencer
            out_offsets (List[float]): list of offsets for each output of the qblox module
        """

        awg_sequencers: Sequence[AWGQbloxSequencer]
        out_offsets: List[float]

        def __post_init__(self):
            """build AWGQbloxSequencer"""
            if (
                self.num_sequencers <= 0
                or self.num_sequencers > QbloxModule._NUM_MAX_SEQUENCERS  # pylint: disable=protected-access
            ):
                raise ValueError(
                    "The number of sequencers must be greater than 0 and less or equal than "
                    + f"{QbloxModule._NUM_MAX_SEQUENCERS}. Received: {self.num_sequencers}"  # pylint: disable=protected-access
                )
            if len(self.awg_sequencers) != self.num_sequencers:
                raise ValueError(
                    f"The number of sequencers: {self.num_sequencers} does not match"
                    + f" the number of AWG Sequencers settings specified: {len(self.awg_sequencers)}"
                )

            self.awg_sequencers = [
                AWGQbloxSequencer(**sequencer)
                if isinstance(sequencer, dict)
                else sequencer  # pylint: disable=not-a-mapping
                for sequencer in self.awg_sequencers
            ]
            super().__post_init__()
            if len(self.awg_iq_channels) > QbloxModule._NUM_MAX_AWG_IQ_CHANNELS:  # pylint: disable=protected-access
                raise ValueError(
                    "The number of AWG IQ channels must be less or equal than "
                    + f"{QbloxModule._NUM_MAX_AWG_IQ_CHANNELS}. Received: {len(self.awg_iq_channels)}"  # pylint: disable=protected-access
                )

    settings: QbloxModuleSettings
    device: Pulsar | QcmQrm
    # Cache containing the last compiled pulse schedule for each sequencer
    _cache: Dict[int, PulseBusSchedule] = {}

    def __init__(self, settings: dict):
        # The sequences dictionary contains all the compiled sequences for each sequencer and a flag indicating whether
        # the sequence has been uploaded or not
        self.sequences: Dict[int, Tuple[Sequence, bool]] = {}  # {sequencer_idx: (program, True), ...}
        # TODO: Set this attribute during initialization of the instrument
        self.nshots: int | None = None
        self.repetition_duration: int | None = None
        super().__init__(settings=settings)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        self._map_outputs()
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            self._set_nco(sequencer_id=sequencer_id)
            self._set_gain_path0(value=sequencer.gain_path0, sequencer_id=sequencer_id)
            self._set_gain_path1(value=sequencer.gain_path1, sequencer_id=sequencer_id)
            self._set_offset_path0(value=sequencer.offset_path0, sequencer_id=sequencer_id)
            self._set_offset_path1(value=sequencer.offset_path1, sequencer_id=sequencer_id)
            self._set_hardware_modulation(value=sequencer.hardware_modulation, sequencer_id=sequencer_id)
            self._set_sync_enabled(value=cast(AWGQbloxSequencer, sequencer).sync_enabled, sequencer_id=sequencer_id)
            self._set_gain_imbalance(value=sequencer.gain_imbalance, sequencer_id=sequencer_id)
            self._set_phase_imbalance(value=sequencer.phase_imbalance, sequencer_id=sequencer_id)

        for idx, offset in enumerate(self.out_offsets):
            self._set_out_offset(output=idx, value=offset)

    @property
    def module_type(self):
        """returns the qblox module type. Options: QCM or QRM"""
        return self.device.module_type()

    def _split_schedule_for_sequencers(self, pulse_bus_schedule: PulseBusSchedule) -> List[PulseBusSchedule]:
        """Returns a list of single-frequency PulseBusSchedules for each sequencer.

        Args:
            pulse_bus_schedule (PulseBusSchedule): schedule to split.

        Raises:
            IndexError: if the number of sequencers does not match the number of AWG Sequencers

        Returns:
            List[PulseBusSchedule]: list of single-frequency PulseBusSchedules for each sequencer.
        """
        frequencies = pulse_bus_schedule.frequencies()
        if len(frequencies) > self._NUM_MAX_SEQUENCERS:
            raise IndexError(
                f"The number of frequencies must be less or equal than the number of sequencers. Got {len(frequencies)} frequencies and {self._NUM_MAX_SEQUENCERS} sequencers."
            )
        return [pulse_bus_schedule.with_frequency(frequency) for frequency in frequencies]

    def compile(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int) -> List[QpySequence]:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        This method skips compilation if the pulse schedule is in the cache. Otherwise, the pulse schedule is
        compiled and added into the cache.

        If the number of shots or the repetition duration changes, the cache will be cleared.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration

        Returns:
            List[QpySequence]: list of compiled assembly programs
        """
        if nshots != self.nshots or repetition_duration != self.repetition_duration:
            self.nshots = nshots
            self.repetition_duration = repetition_duration
            self.clear_cache()

        sequencers_pulse_bus_schedule = self._split_schedule_for_sequencers(pulse_bus_schedule=pulse_bus_schedule)
        compiled_sequences = []
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=pulse_bus_schedule.port)
        for sequencer, schedule in zip(sequencers, sequencers_pulse_bus_schedule):
            if sequencer not in self._cache or pulse_bus_schedule != self._cache[sequencer]:
                sequence = self._compile(schedule, sequencer)
                compiled_sequences.append(sequence)
            else:
                compiled_sequences.append(self.sequences[sequencer][0])
        return compiled_sequences

    def _compile(self, pulse_bus_schedule: PulseBusSchedule, sequencer: int) -> QpySequence:
        """Compiles the ``PulseBusSchedule`` into an assembly program and updates the cache and the saved sequences.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            sequencer (int): index of the sequencer to generate the program
        """
        if (n_freqs := len(pulse_bus_schedule.frequencies())) != 1:
            raise ValueError(
                f"The PulseBusSchedule of a sequencer must have exactly one frequency. This instance has {n_freqs}."
            )
        sequence = self._translate_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule, sequencer=sequencer)
        self._cache[sequencer] = pulse_bus_schedule
        self.sequences[sequencer] = (sequence, False)
        return sequence

    def run(self):
        """Run the uploaded program"""
        self.start_sequencer()

    def _translate_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule, sequencer: int):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.
            sequencer (int): index of the sequencer to generate the program

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule)
        acquisitions = self._generate_acquisitions()
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, sequencer=sequencer
        )
        weights = self._generate_weights(sequencer_id=sequencer)
        return QpySequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights.to_dict())

    def _generate_empty_program(self):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
            waveforms (Waveforms): Waveforms.

        Returns:
            Program: Q1ASM program.
        """
        # Define program's blocks
        program = Program()
        avg_loop = Loop(name="average", begin=int(self.nshots))  # type: ignore
        program.append_block(avg_loop)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=stop)
        wait_time = self.repetition_duration
        if wait_time > self._MIN_WAIT_TIME:
            avg_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access
        return program

    def _generate_program(self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms, sequencer: int):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): pulse sequence
            waveforms (Waveforms): waveforms
            sequencer (int): index of the sequencer to generate the program

        Returns:
            Program: Q1ASM program.
        """
        # Define program's blocks
        program = Program()
        avg_loop = Loop(name="average", begin=int(self.nshots))  # type: ignore
        program.append_block(avg_loop)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=stop)
        timeline = pulse_bus_schedule.timeline
        if timeline[0].start_time != 0:  # TODO: Make sure that start time of Pulse is 0 or bigger than 4
            avg_loop.append_component(Wait(wait_time=int(timeline[0].start_time)))

        for i, pulse_event in enumerate(timeline):
            waveform_pair = waveforms.find_pair_by_name(pulse_event.pulse.label())
            wait_time = timeline[i + 1].start_time - pulse_event.start_time if (i < (len(timeline) - 1)) else 4
            avg_loop.append_component(ResetPh())
            avg_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=int(wait_time),
                )
            )
        self._append_acquire_instruction(loop=avg_loop, bin_index=0, sequencer_id=sequencer)
        wait_time = self.repetition_duration - avg_loop.duration_iter
        if wait_time > self._MIN_WAIT_TIME:
            avg_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access
        return program

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "default", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        # FIXME: is it really necessary to generate acquisitions for a QCM??
        acquisitions = Acquisitions()
        acquisitions.add(name="default", num_bins=1, index=0)
        return acquisitions

    @abstractmethod
    def _generate_weights(self, sequencer_id: int) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """

    @abstractmethod
    def _append_acquire_instruction(self, loop: Loop, bin_index: Register | int, sequencer_id: int):
        """Append an acquire instruction to the loop."""

    def start_sequencer(self):
        """Start sequencer and execute the uploaded instructions."""
        for sequencer in self.awg_sequencers:
            self.device.arm_sequencer(sequencer=sequencer.identifier)
            self.device.start_sequencer(sequencer=sequencer.identifier)

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""
        if channel_id is None:
            if self.num_sequencers == 1:
                channel_id = 0
            else:
                raise ValueError("channel not specified to update instrument")

        if channel_id > self.num_sequencers - 1:
            raise ValueError(
                f"the specified channel id:{channel_id} is out of range. Number of sequencers is {self.num_sequencers}"
            )
        if parameter == Parameter.GAIN:
            self._set_gain(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_PATH0:
            self._set_gain_path0(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_PATH1:
            self._set_gain_path1(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.OFFSET_PATH0:
            self._set_offset_path0(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.OFFSET_PATH1:
            self._set_offset_path1(value=value, sequencer_id=channel_id)
            return
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            self._set_out_offset(output=output, value=value)
            return
        if parameter == Parameter.OFFSET_I:
            self._set_offset_i(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.OFFSET_Q:
            self._set_offset_q(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.IF:
            self._set_frequency(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.HARDWARE_MODULATION:
            self._set_hardware_modulation(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.SYNC_ENABLED:
            self._set_sync_enabled(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.NUM_BINS:
            self._set_num_bins(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_IMBALANCE:
            self._set_gain_imbalance(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.PHASE_IMBALANCE:
            self._set_phase_imbalance(value=value, sequencer_id=channel_id)
            return
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @Instrument.CheckParameterValueFloatOrInt
    def _set_num_bins(self, value: float | str | bool, sequencer_id: int):
        """set num_bins for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        if int(value) > self._MAX_BINS:
            raise ValueError(f"Value {value} greater than maximum bins: {self._MAX_BINS}")
        cast(AWGQbloxSequencer, self.awg_sequencers[sequencer_id]).num_bins = int(value)

    @Instrument.CheckParameterValueBool
    def _set_sync_enabled(self, value: float | str | bool, sequencer_id: int):
        """set sync enabled for the specific channel

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        cast(AWGQbloxSequencer, self.awg_sequencers[sequencer_id]).sync_enabled = bool(value)
        self.device.sequencers[sequencer_id].sync_en(bool(value))

    @Instrument.CheckParameterValueBool
    def _set_hardware_modulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware modulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self.awg_sequencers[sequencer_id].hardware_modulation = bool(value)
        self.device.sequencers[sequencer_id].mod_en_awg(bool(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_frequency(self, value: float | str | bool, sequencer_id: int):
        """set frequency

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.awg_sequencers[sequencer_id].intermediate_frequency = float(value)
        self.device.sequencers[sequencer_id].nco_freq(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_path0(self, value: float | str | bool, sequencer_id: int):
        """set offset path0

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.awg_sequencers[sequencer_id].offset_path0 = float(value)
        self.device.sequencers[sequencer_id].offset_awg_path0(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_path1(self, value: float | str | bool, sequencer_id: int):
        """set offset path1

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.awg_sequencers[sequencer_id].offset_path1 = float(value)
        self.device.sequencers[sequencer_id].offset_awg_path1(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_out_offset(self, output: int, value: float | str | bool):
        """Set output offsets of the Qblox device.

        Args:
            output (int): output to update
            value (float | str | bool): value to update

        Raises:
            ValueError: when value type is not float or int
        """
        if output > len(self.out_offsets):
            raise IndexError(
                f"Output {output} is out of range. The runcard has only {len(self.out_offsets)} output offsets defined."
                " Please update the list of output offsets of the runcard such that it contains a value for each "
                "output of the device."
            )
        self.out_offsets[output] = value
        getattr(self.device, f"out{output}_offset")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_i(self, value: float | str | bool, sequencer_id: int):
        """set offset I

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        path_id = self.get_sequencer_path_id_mapped_to_i_channel(sequencer_id=sequencer_id)
        if path_id == AWGSequencerPathIdentifier.PATH0:
            self._set_offset_path0(value=value, sequencer_id=sequencer_id)
            return
        self._set_offset_path1(value=value, sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_q(self, value: float | str | bool, sequencer_id: int):
        """set offset Q

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        path_id = self.get_sequencer_path_id_mapped_to_q_channel(sequencer_id=sequencer_id)
        if path_id == AWGSequencerPathIdentifier.PATH1:
            self._set_offset_path1(value=value, sequencer_id=sequencer_id)
            return
        self._set_offset_path0(value=value, sequencer_id=sequencer_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_path0(self, value: float | str | bool, sequencer_id: int):
        """set gain path0

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.awg_sequencers[sequencer_id].gain_path0 = float(value)
        self.device.sequencers[sequencer_id].gain_awg_path0(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_path1(self, value: float | str | bool, sequencer_id: int):
        """set gain path1

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.awg_sequencers[sequencer_id].gain_path1 = float(value)
        self.device.sequencers[sequencer_id].gain_awg_path1(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain(self, value: float | str | bool, sequencer_id: int):
        """set gain

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self._set_gain_path0(value=value, sequencer_id=sequencer_id)
        self._set_gain_path1(value=value, sequencer_id=sequencer_id)

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop the QBlox sequencer from sending pulses."""
        for seq_idx in range(self.num_sequencers):
            self.device.stop_sequencer(sequencer=seq_idx)

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Turn on an instrument."""

    def clear_cache(self):
        """Empty cache."""
        self._cache = {}

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.clear_cache()
        self.device.reset()

    def upload(self):
        """Upload all the previously compiled programs to its corresponding sequencers.

        This method must be called after the method ``compile``."""
        if self.nshots is None or self.repetition_duration is None:
            raise ValueError("Please compile the circuit before uploading it to the device.")
        empty_program = self._generate_empty_program()
        empty_sequence = QpySequence(
            program=empty_program, waveforms=Waveforms(), acquisitions=Acquisitions(), weights={}
        )
        for seq_idx in range(self.num_sequencers):
            if seq_idx not in self.sequences:
                self.sequences[seq_idx] = (empty_sequence, False)
            sequence, uploaded = self.sequences[seq_idx]
            if not uploaded:
                logger.info("Sequence program: \n %s", repr(sequence._program))  # pylint: disable=protected-access
                self.device.sequencers[seq_idx].sequence(sequence.todict())
                self.sequences[seq_idx] = (sequence, True)

    def _set_nco(self, sequencer_id: int):
        """Enable modulation of pulses and setup NCO frequency."""
        if self.awg_sequencers[sequencer_id].hardware_modulation:
            self._set_hardware_modulation(
                value=self.awg_sequencers[sequencer_id].hardware_modulation, sequencer_id=sequencer_id
            )
            self._set_frequency(
                value=self.awg_sequencers[sequencer_id].intermediate_frequency, sequencer_id=sequencer_id
            )

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_imbalance(self, value: float | str | bool, sequencer_id: int):
        """Set I and Q gain imbalance of sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """

        self.awg_sequencers[sequencer_id].gain_imbalance = float(value)
        self.device.sequencers[sequencer_id].mixer_corr_gain_ratio(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_phase_imbalance(self, value: float | str | bool, sequencer_id: int):
        """Set I and Q phase imbalance of sequencer.

         Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self.awg_sequencers[sequencer_id].phase_imbalance = float(value)
        self.device.sequencers[sequencer_id].mixer_corr_phase_offset_degree(float(value))

    def _map_outputs(self):
        """Disable all connections and map sequencer paths with output channels."""
        # Disable all connections
        for sequencer, out in itertools.product(self.device.sequencers, range(self._NUM_MAX_SEQUENCERS)):
            if hasattr(sequencer, f"channel_map_path{out % 2}_out{out}_en"):
                sequencer.set(f"channel_map_path{out % 2}_out{out}_en", False)

        for sequencer in self.awg_sequencers:
            if sequencer.path0 is not None:
                self.device.sequencers[sequencer.identifier].set(
                    f"channel_map_path0_out{sequencer.out_id_path0}_en", True
                )
            if sequencer.path1 is not None:
                self.device.sequencers[sequencer.identifier].set(
                    f"channel_map_path1_out{sequencer.out_id_path1}_en", True
                )

    def _generate_waveforms(self, pulse_bus_schedule: PulseBusSchedule):
        """Generate I and Q waveforms from a PulseSequence object.
        Args:
            pulse_bus_schedule (PulseBusSchedule): PulseSequence object.
        Returns:
            Waveforms: Waveforms object containing the generated waveforms.
        """
        waveforms = Waveforms()

        unique_pulses: List[Tuple[int, PulseShape]] = []

        for pulse_event in pulse_bus_schedule.timeline:
            if (pulse_event.duration, pulse_event.pulse.pulse_shape) not in unique_pulses:
                unique_pulses.append((pulse_event.duration, pulse_event.pulse.pulse_shape))
                envelope = pulse_event.pulse.envelope(amplitude=1)
                real = np.real(envelope)
                imag = np.imag(envelope)
                waveforms.add_pair((real, imag), name=pulse_event.pulse.label())

        return waveforms

    @property
    def final_wait_time(self) -> int:
        """QbloxPulsar 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self._MIN_WAIT_TIME

    @property
    def out_offsets(self):
        """Returns the offsets of each output of the qblox module."""
        return self.settings.out_offsets
