# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Qblox module class"""
import itertools
from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence, cast

import numpy as np
from qpysequence import Acquisitions, Program
from qpysequence import Sequence as QpySequence
from qpysequence import Waveforms, Weights
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Register
from qpysequence.program.instructions import Play, ResetPh, SetAwgGain, SetPh, Stop
from qpysequence.utils.constants import AWG_MAX_GAIN

from qililab.config import logger
from qililab.instruments.awg import AWG
from qililab.instruments.awg_settings import AWGQbloxSequencer
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
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxModuleSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            awg_sequencers (Sequence[AWGQbloxSequencer]): list of settings for each sequencer
            out_offsets (list[float]): list of offsets for each output of the qblox module
        """

        awg_sequencers: Sequence[AWGQbloxSequencer]
        out_offsets: list[float]

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

    settings: QbloxModuleSettings
    device: Pulsar | QcmQrm
    # Cache containing the last compiled pulse schedule for each sequencer
    _cache: dict[int, PulseBusSchedule] = {}

    def __init__(self, settings: dict):
        # The sequences dictionary contains all the compiled sequences for each sequencer and a flag indicating whether
        # the sequence has been uploaded or not
        self.sequences: dict[int, tuple[QpySequence, bool]] = {}  # {sequencer_idx: (program, True), ...}
        # TODO: Set this attribute during initialization of the instrument
        self.nshots: int | None = None
        self.num_bins: int = 1
        self.repetition_duration: int | None = None
        super().__init__(settings=settings)

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        self._map_outputs()
        self.clear_cache()
        for sequencer in self.awg_sequencers:
            sequencer_id = sequencer.identifier
            # Set `sync_en` flag to False (this value will be set to True if the sequencer is used in the execution)
            self.device.sequencers[sequencer_id].sync_en(False)
            self._set_nco(sequencer_id=sequencer_id)
            self._set_gain_i(value=sequencer.gain_i, sequencer_id=sequencer_id)
            self._set_gain_q(value=sequencer.gain_q, sequencer_id=sequencer_id)
            self._set_offset_i(value=sequencer.offset_i, sequencer_id=sequencer_id)
            self._set_offset_q(value=sequencer.offset_q, sequencer_id=sequencer_id)
            self._set_hardware_modulation(value=sequencer.hardware_modulation, sequencer_id=sequencer_id)
            self._set_gain_imbalance(value=sequencer.gain_imbalance, sequencer_id=sequencer_id)
            self._set_phase_imbalance(value=sequencer.phase_imbalance, sequencer_id=sequencer_id)
            ALL_ON = 15  # 1111 in binary
            self._set_markers(value=ALL_ON, sequencer_id=sequencer_id)

        for idx, offset in enumerate(self.out_offsets):
            self._set_out_offset(output=idx, value=offset)

    def desync_sequencers(self) -> None:
        """Desyncs all sequencers."""
        for sequencer in self.awg_sequencers:
            self.device.sequencers[sequencer.identifier].sync_en(False)

    @property
    def module_type(self):
        """returns the qblox module type. Options: QCM or QRM"""
        return self.device.module_type()

    def compile(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ) -> list[QpySequence]:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        This method skips compilation if the pulse schedule is in the cache. Otherwise, the pulse schedule is
        compiled and added into the cache.

        If the number of shots or the repetition duration changes, the cache will be cleared.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins

        Returns:
            list[QpySequence]: list of compiled assembly programs
        """
        if nshots != self.nshots or repetition_duration != self.repetition_duration or num_bins != self.num_bins:
            self.nshots = nshots
            self.repetition_duration = repetition_duration
            self.num_bins = num_bins
            self.clear_cache()

        compiled_sequences = []
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=pulse_bus_schedule.port)
        for sequencer in sequencers:
            if pulse_bus_schedule != self._cache.get(sequencer.identifier):
                sequence = self._compile(pulse_bus_schedule, sequencer)
                compiled_sequences.append(sequence)
            else:
                compiled_sequences.append(self.sequences[sequencer.identifier][0])
        return compiled_sequences

    def _compile(self, pulse_bus_schedule: PulseBusSchedule, sequencer: AWGQbloxSequencer) -> QpySequence:
        """Compiles the ``PulseBusSchedule`` into an assembly program and updates the cache and the saved sequences.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
            sequencer (int): index of the sequencer to generate the program
        """
        sequence = self._translate_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule, sequencer=sequencer)
        self._cache[sequencer.identifier] = pulse_bus_schedule
        self.sequences[sequencer.identifier] = (sequence, False)
        return sequence

    def run(self, port: str):
        """Run the uploaded program"""
        self.start_sequencer(port=port)

    def _translate_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule, sequencer: AWGQbloxSequencer):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.
            sequencer (int): index of the sequencer to generate the program

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule, sequencer=sequencer)
        acquisitions = self._generate_acquisitions()
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, sequencer=sequencer.identifier
        )
        weights = self._generate_weights(sequencer=sequencer)
        return QpySequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)

    def _generate_program(  # pylint: disable=too-many-locals
        self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms, sequencer: int
    ):
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
        start = Block(name="start")
        start.append_component(ResetPh())
        program.append_block(block=start)
        # Create registers with 0 and 1 (necessary for qblox)
        weight_registers = Register(), Register()
        self._init_weights_registers(registers=weight_registers, values=(0, 1), program=program)
        avg_loop = Loop(name="average", begin=int(self.nshots))  # type: ignore
        bin_loop = Loop(name="bin", begin=0, end=self.num_bins, step=1)
        avg_loop.append_component(bin_loop)
        program.append_block(avg_loop)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=stop)
        timeline = pulse_bus_schedule.timeline
        if len(timeline) > 0 and timeline[0].start_time != 0:
            bin_loop.append_component(long_wait(wait_time=int(timeline[0].start_time)))

        for i, pulse_event in enumerate(timeline):
            waveform_pair = waveforms.find_pair_by_name(pulse_event.pulse.label())
            wait_time = timeline[i + 1].start_time - pulse_event.start_time if (i < (len(timeline) - 1)) else 4
            phase = int((pulse_event.pulse.phase % (2 * np.pi)) * 1e9 / (2 * np.pi))
            gain = int(np.abs(pulse_event.pulse.amplitude) * AWG_MAX_GAIN)  # np.abs() needed for negative pulses
            bin_loop.append_component(SetAwgGain(gain_0=gain, gain_1=gain))
            bin_loop.append_component(SetPh(phase=phase))
            bin_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=int(wait_time),
                )
            )
        self._append_acquire_instruction(
            loop=bin_loop, bin_index=bin_loop.counter_register, sequencer_id=sequencer, weight_regs=weight_registers
        )
        if self.repetition_duration is not None:
            wait_time = self.repetition_duration - bin_loop.duration_iter
            if wait_time > self._MIN_WAIT_TIME:
                bin_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access
        return program

    def _init_weights_registers(self, registers: tuple[Register, Register], values: tuple[int, int], program: Program):
        """Initialize the weights `registers` to the `values` specified and place the required instructions in the
        setup block of the `program`."""

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "default", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        # FIXME: is it really necessary to generate acquisitions for a QCM??
        acquisitions = Acquisitions()
        acquisitions.add(name="default", num_bins=self.num_bins, index=0)
        return acquisitions

    @abstractmethod
    def _generate_weights(self, sequencer: AWGQbloxSequencer) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """

    @abstractmethod
    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, sequencer_id: int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""

    def start_sequencer(self, port: str):
        """Start sequencer and execute the uploaded instructions."""
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            if sequencer.identifier in self.sequences:
                self.device.arm_sequencer(sequencer=sequencer.identifier)
                self.device.start_sequencer(sequencer=sequencer.identifier)

    @Instrument.CheckDeviceInitialized
    def setup(  # pylint: disable=too-many-branches, too-many-return-statements
        self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None, port_id: str | None = None
    ):
        """Set Qblox instrument calibration settings."""
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            self._set_out_offset(output=output, value=value)
            return

        if channel_id is None:
            if port_id is not None:
                channel_id = self.get_sequencers_from_chip_port_id(chip_port_id=port_id)[0].identifier
            elif self.num_sequencers == 1:
                channel_id = 0
            else:
                raise ParameterNotFound(f"Cannot update parameter {parameter.value} without specifying a channel_id.")

        if channel_id > self.num_sequencers - 1:
            raise ParameterNotFound(
                f"the specified channel id:{channel_id} is out of range. Number of sequencers is {self.num_sequencers}"
            )
        if parameter == Parameter.GAIN:
            self._set_gain(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_I:
            self._set_gain_i(value=value, sequencer_id=channel_id)
            return
        if parameter == Parameter.GAIN_Q:
            self._set_gain_q(value=value, sequencer_id=channel_id)
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

    def get(self, parameter: Parameter, channel_id: int | None = None, port_id: str | None = None):
        """Get instrument parameter.

        Args:
            parameter (Parameter): Name of the parameter to get.
            channel_id (int | None): Channel identifier of the parameter to update.
        """
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            return self.out_offsets[output]

        if channel_id is None:
            if port_id is not None:
                channel_id = self.get_sequencers_from_chip_port_id(chip_port_id=port_id)[0].identifier
            elif self.num_sequencers == 1:
                channel_id = 0
            else:
                raise ParameterNotFound(f"Cannot update parameter {parameter.value} without specifying a channel_id.")

        sequencer = self._get_sequencer_by_id(id=channel_id)

        if parameter == Parameter.GAIN:
            return sequencer.gain_i, sequencer.gain_q

        if hasattr(sequencer, parameter.value):
            return getattr(sequencer, parameter.value)

        raise ParameterNotFound(f"Cannot find parameter {parameter.value} in instrument {self.alias}")

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
        cast(AWGQbloxSequencer, self._get_sequencer_by_id(id=sequencer_id)).num_bins = int(value)

    @Instrument.CheckParameterValueBool
    def _set_hardware_modulation(self, value: float | str | bool, sequencer_id: int):
        """set hardware modulation

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not bool
        """
        self._get_sequencer_by_id(id=sequencer_id).hardware_modulation = bool(value)
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
        self._get_sequencer_by_id(id=sequencer_id).intermediate_frequency = float(value)
        self.device.sequencers[sequencer_id].nco_freq(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_i(self, value: float | str | bool, sequencer_id: int):
        """Set the offset of the I channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).offset_i = float(value)
        # update value in the instrument
        path = self._get_sequencer_by_id(id=sequencer_id).path_i
        sequencer = self.device.sequencers[sequencer_id]
        getattr(sequencer, f"offset_awg_path{path}")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_offset_q(self, value: float | str | bool, sequencer_id: int):
        """Set the offset of the Q channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).offset_q = float(value)
        # update value in the instrument
        path = self._get_sequencer_by_id(id=sequencer_id).path_q
        sequencer = self.device.sequencers[sequencer_id]
        getattr(sequencer, f"offset_awg_path{path}")(float(value))

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
    def _set_gain_i(self, value: float | str | bool, sequencer_id: int):
        """Set the gain of the I channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).gain_i = float(value)
        # update value in the instrument
        path = self._get_sequencer_by_id(id=sequencer_id).path_i
        sequencer = self.device.sequencers[sequencer_id]
        getattr(sequencer, f"gain_awg_path{path}")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain_q(self, value: float | str | bool, sequencer_id: int):
        """Set the gain of the Q channel of the given sequencer.

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        # update value in qililab
        self._get_sequencer_by_id(id=sequencer_id).gain_q = float(value)
        # update value in the instrument
        path = self._get_sequencer_by_id(id=sequencer_id).path_q
        sequencer = self.device.sequencers[sequencer_id]
        getattr(sequencer, f"gain_awg_path{path}")(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_gain(self, value: float | str | bool, sequencer_id: int):
        """set gain

        Args:
            value (float | str | bool): value to update
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not float
        """
        self._set_gain_i(value=value, sequencer_id=sequencer_id)
        self._set_gain_q(value=value, sequencer_id=sequencer_id)

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
        self.sequences = {}

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.clear_cache()
        self.device.reset()

    def upload(self, port: str):
        """Upload all the previously compiled programs to its corresponding sequencers.

        This method must be called after the method ``compile``."""
        if self.nshots is None or self.repetition_duration is None:
            raise ValueError("Please compile the circuit before uploading it to the device.")
        sequencers = self.get_sequencers_from_chip_port_id(chip_port_id=port)
        for sequencer in sequencers:
            if (seq_idx := sequencer.identifier) in self.sequences:
                sequence, uploaded = self.sequences[seq_idx]
                self.device.sequencers[seq_idx].sync_en(True)
                if not uploaded:
                    logger.info("Sequence program: \n %s", repr(sequence._program))  # pylint: disable=protected-access
                    self.device.sequencers[seq_idx].sequence(sequence.todict())
                    self.sequences[seq_idx] = (sequence, True)

    def _set_nco(self, sequencer_id: int):
        """Enable modulation of pulses and setup NCO frequency."""
        if self._get_sequencer_by_id(id=sequencer_id).hardware_modulation:
            self._set_hardware_modulation(
                value=self._get_sequencer_by_id(id=sequencer_id).hardware_modulation, sequencer_id=sequencer_id
            )
            self._set_frequency(
                value=self._get_sequencer_by_id(id=sequencer_id).intermediate_frequency, sequencer_id=sequencer_id
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

        self._get_sequencer_by_id(id=sequencer_id).gain_imbalance = float(value)
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
        self._get_sequencer_by_id(id=sequencer_id).phase_imbalance = float(value)
        self.device.sequencers[sequencer_id].mixer_corr_phase_offset_degree(float(value))

    @Instrument.CheckParameterValueFloatOrInt
    def _set_markers(self, value: int, sequencer_id: int):
        """Set markers ON/OFF on qblox modules.

        For the RF modules, this command is also used to enable/disable:
            - The 2 outputs (for the QCM-RF).
            - The input and the output (for QRM-RF).

         Args:
            value (int): ON/OFF of the 4 markers in binary (range: 0-15 -> (0000)-(1111)). For the RF modules, the
                first 2 bits correspond to the ON/OFF value of the outputs/inputs and the last 2 bits correspond
                to the 2 markers.
            sequencer_id (int): sequencer to update the value

        Raises:
            ValueError: when value type is not int
        """
        self.device.sequencers[sequencer_id].marker_ovr_en(True)
        self.device.sequencers[sequencer_id].marker_ovr_value(value)

    def _map_outputs(self):
        """Disable all connections and map sequencer paths with output channels."""
        # Disable all connections
        for sequencer, out in itertools.product(self.device.sequencers, range(self._NUM_MAX_SEQUENCERS)):
            if hasattr(sequencer, f"channel_map_path{out % 2}_out{out}_en"):
                sequencer.set(f"channel_map_path{out % 2}_out{out}_en", False)

        for sequencer in self.awg_sequencers:
            if sequencer.output_i is not None:
                self.device.sequencers[sequencer.identifier].set(
                    f"channel_map_path{sequencer.path_i}_out{sequencer.output_i}_en", True
                )
            if sequencer.output_q is not None:
                self.device.sequencers[sequencer.identifier].set(
                    f"channel_map_path{sequencer.path_q}_out{sequencer.output_q}_en", True
                )

    def _generate_waveforms(self, pulse_bus_schedule: PulseBusSchedule, sequencer: AWGQbloxSequencer):
        """Generate I and Q waveforms from a PulseSequence object.
        Args:
            pulse_bus_schedule (PulseBusSchedule): PulseSequence object.
        Returns:
            Waveforms: Waveforms object containing the generated waveforms.
        """
        waveforms = Waveforms()

        unique_pulses: list[tuple[int, PulseShape]] = []

        for pulse_event in pulse_bus_schedule.timeline:
            if (pulse_event.duration, pulse_event.pulse.pulse_shape) not in unique_pulses:
                unique_pulses.append((pulse_event.duration, pulse_event.pulse.pulse_shape))
                amp = pulse_event.pulse.amplitude
                sign = 1 if amp >= 0 else -1
                envelope = pulse_event.envelope(amplitude=sign * 1.0)
                real = np.real(envelope)
                imag = np.imag(envelope)
                pair = (real, imag)
                if (sequencer.path_i, sequencer.path_q) == (1, 0):
                    pair = pair[::-1]  # swap paths
                waveforms.add_pair(pair=pair, name=pulse_event.pulse.label())

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

    def _get_sequencer_by_id(self, id: int):  # pylint: disable=redefined-builtin
        """Returns a sequencer with the given `id`."

        Args:
            id (int): Id of the sequencer.

        Raises:
            IndexError: There is no sequencer with the given `id`.

        Returns:
            AWGQbloxSequencer: Sequencer with the given `id`.
        """
        for sequencer in self.awg_sequencers:
            if sequencer.identifier == id:
                return sequencer
        raise IndexError(f"There is no sequencer with id={id}.")
