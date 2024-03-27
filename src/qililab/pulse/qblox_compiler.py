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

import numpy as np
from qpysequence import Acquisitions, Program
from qpysequence import Sequence as QpySequence
from qpysequence import Waveforms, Weights
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Register
from qpysequence.program.instructions import Acquire, AcquireWeighed, Move, Play, ResetPh, SetAwgGain, SetPh, Stop, Wait
from qpysequence.utils.constants import AWG_MAX_GAIN, INST_MAX_WAIT

from qililab.config import logger
from qililab.instruments.awg_settings import AWGQbloxADCSequencer, AWGQbloxSequencer
from qililab.instruments.qblox import QbloxModule
from qililab.pulse.pulse_bus_schedule import PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent
from qililab.pulse.pulse_schedule import PulseSchedule
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import InstrumentName


class QbloxCompiler:  # pylint: disable=too-many-locals
    """Qblox compiler for pulse schedules. Its only public method is `compile`, which compiles a pulse schedule to qpysequences (see docs for `QBloxCompiler.compile`).
    The class object is meant to be initialized once, with `compile` running as many times as necessary. This way the class attributes do not have to be initialized
    at each single compilation.

    Args:
        platform (Platform): Platform object representing the laboratory setup used to control quantum devices.
    Raises:
        ValueError: at init if no readout module (QRM) is found in platform.
    """

    def __init__(self, platform):
        self.qblox_modules = [
            instrument for instrument in platform.instruments.elements if isinstance(instrument, QbloxModule)
        ]
        self.buses = platform.buses
        # init variables as empty
        self.nshots = None
        self.num_bins = None
        self.repetition_duration = None
        self.readout_modules = [InstrumentName.QBLOX_QRM, InstrumentName.QRMRF]
        self.control_modules = [InstrumentName.QBLOX_QCM, InstrumentName.QCMRF]

        if all(
            qblox.name not in self.readout_modules for qblox in self.qblox_modules
        ):  # Raise error if qrm is not found
            raise ValueError("No QRM modules found in platform instruments")

    def compile(
        self, pulse_schedule: PulseSchedule, num_avg: int, repetition_duration: int, num_bins: int
    ) -> dict[str, list[QpySequence]]:
        """Compiles a given pulse schedule to a Sequence (QpySequence). If the compiler object is created and not
        reinitialized between executions, previously run Sequences and PulseBusSchedules are saved to the corresponding's
        qblox_module sequences and cache, respectively. They can then be loaded from the stored data instead of being
        compiled again.

        Args:
            pulse_schedule (PulseSchedule): PulseSchedule to be executed
            num_avg (int): hardware average - number of times to average execution over
            repetition_duration (int): fixed execution duration. Execution always lasts `repetition_duration` ns. If execution is shorter than that, a wait time of `repetition_duration` - circuit_execution_time is added (this is used for qubti relaxation)
            num_bins (int): number of shots to execute

        Raises:
            ValueError: if circuit execution time is longer than `repetition_duration`
            NotImplementedError: if more than one readout module is found connected to the platform

        Returns:
            dict[str, list[QpySequence]]: dictionary where the keys correspond to the bus which has to execute a list of QpySequences, given in the values
        """
        if num_avg != self.nshots or repetition_duration != self.repetition_duration or num_bins != self.num_bins:
            self.nshots = num_avg
            self.repetition_duration = repetition_duration
            self.num_bins = num_bins
            for qblox_module in self.qblox_modules:
                qblox_module.clear_cache()

        sequencer_qrm_bus_schedules, sequencer_qcm_bus_schedules = self.get_sequencer_schedule(
            pulse_schedule, self.qblox_modules
        )

        compiled_sequences = {}  # type: dict[str, list[QpySequence]]

        # generally a sequencer_schedule is the schedule sent to a specific bus, except for readout,
        # where multiple schedules for different sequencers are sent to the same bus
        for sequencer, sequencer_schedule in sequencer_qrm_bus_schedules + sequencer_qcm_bus_schedules:
            # check if circuit lasts longer than repetition duration
            end_time = None if len(sequencer_schedule.timeline) == 0 else sequencer_schedule.timeline[-1].end_time
            if end_time is not None and end_time > self.repetition_duration:
                raise ValueError(
                    f"Circuit execution time cannnot be longer than repetition duration but found circuit time {end_time } > {repetition_duration} for qubit {sequencer_schedule.qubit}"
                )
            # get qblox module for this sequencer
            qblox_module = self._get_instrument_from_sequencer(sequencer)
            bus_alias = self.buses.get(sequencer_schedule.port).alias
            # create empty list if key does not exist
            if bus_alias not in compiled_sequences:
                compiled_sequences[bus_alias] = []
            # if the schedule is already compiled get it from the module's sequences
            if sequencer_schedule == qblox_module.cache.get(
                sequencer.identifier
            ):  # if it's already cached then dont compile
                compiled_sequences[bus_alias].append(qblox_module.sequences[sequencer.identifier])
                # If the schedule is in the cache, delete the acquisition data (if uploaded) # FIXME: acquisitions should be deleted after acquisitions and not at compilation
                if qblox_module.name in self.readout_modules and hasattr(
                    qblox_module, "device"
                ):  # TODO: remove hasattr when the fixme above is done
                    qblox_module.device.delete_acquisition_data(sequencer=sequencer.identifier, all=True)

            else:
                # compile the sequences
                sequence = self._translate_pulse_bus_schedule(sequencer_schedule, sequencer)
                compiled_sequences[bus_alias].append(sequence)
                qblox_module.cache[sequencer.identifier] = sequencer_schedule
                qblox_module.sequences[sequencer.identifier] = sequence

        # check for sequences which where not in the PulseSchedule but are uploaded to a given qrm and erase them from cache
        # this is only needed for the qrm since it has multiple sequencers for the same bus
        for qrm in self.qblox_modules:
            # skip if not qrm
            if qrm.name not in self.readout_modules:
                continue
            compiled_seqs = {
                sequencer.identifier for sequencer, _ in sequencer_qrm_bus_schedules if sequencer in qrm.awg_sequencers
            }
            # pop from cache if a sequencer id is cached in the qrm but not present in compiled sequences for that qrm
            for seq_id in [cached_seq_id for cached_seq_id in qrm.cache.keys() if cached_seq_id not in compiled_seqs]:
                _ = qrm.cache.pop(seq_id)
                _ = qrm.sequences.pop(seq_id)

        return compiled_sequences

    def _translate_pulse_bus_schedule(
        self, pulse_bus_schedule: PulseBusSchedule, sequencer: AWGQbloxSequencer
    ) -> QpySequence:
        """Translate a pulse sequence into a Q1ASM program, a waveform dictionary and
        acquisitions dictionary (that is, a QpySequence sequence).

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.
            sequencer (AWGQbloxSequencer): sequencer to generate the program

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule)
        acquisitions = self._generate_acquisitions(sequencer, timeline=pulse_bus_schedule.timeline)
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, sequencer=sequencer
        )
        weights = self._generate_weights(sequencer=sequencer)  # type: ignore
        return QpySequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)

    def _generate_waveforms(self, pulse_bus_schedule: PulseBusSchedule):
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
                waveforms.add_pair(pair=pair, name=pulse_event.pulse.label())

        return waveforms

    def _generate_acquisitions(self, sequencer: AWGQbloxSequencer, timeline: list[PulseEvent]) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "default", with num_bins = 1
        and index = 0.

        Args:
            sequencer (AWGQbloxSequencer): sequencer to which we generate the acquisitions dictionary
            timeline (list[PulseEvent]): time ordered list of pulse events to play

        Returns:
            Acquisitions: Acquisitions object.
        """
        # FIXME: is it really necessary to generate acquisitions for a QCM??
        acquisitions = Acquisitions()
        if self._get_instrument_from_sequencer(sequencer).name in self.control_modules:
            return acquisitions
        for i, pulse in enumerate(timeline):
            acquisitions.add(name=f"acq_q{pulse.qubit}_{i}", num_bins=self.num_bins, index=i)
        return acquisitions

    def _generate_program(  # pylint: disable=too-many-locals
        self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms, sequencer: AWGQbloxSequencer
    ) -> Program:
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): pulse sequence
            waveforms (Waveforms): waveforms
            sequencer (int): index of the sequencer to generate the program

        Returns:
            Program: Q1ASM program.
        """
        # get qblox module from sequencer
        qblox_module = self._get_instrument_from_sequencer(sequencer)
        MIN_WAIT = qblox_module._MIN_WAIT_TIME  # pylint: disable=protected-access

        # Define program's blocks
        program = Program()
        start = Block(name="start")
        start.append_component(ResetPh())
        program.append_block(block=start)
        # Create registers with 0 and 1 (necessary for qblox)
        weight_registers = Register(), Register()
        if qblox_module.name in self.readout_modules:
            self._init_weights_registers(registers=weight_registers, program=program)
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
            wait_time = timeline[i + 1].start_time - pulse_event.start_time if (i < (len(timeline) - 1)) else MIN_WAIT

            # Allow wait times longer than INST_MAX_WAIT
            long_wait_time = 0
            if wait_time > INST_MAX_WAIT:
                long_wait_time = wait_time - 2 * MIN_WAIT
                wait_time = 2 * MIN_WAIT
            # Add instrucitons to play the pulse
            phase = int((pulse_event.pulse.phase % (2 * np.pi)) * 1e9 / (2 * np.pi))
            gain = int(np.abs(pulse_event.pulse.amplitude) * AWG_MAX_GAIN)  # np.abs() needed for negative pulses
            bin_loop.append_component(SetAwgGain(gain_0=gain, gain_1=gain))
            bin_loop.append_component(SetPh(phase=phase))
            bin_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    # wait until next pulse if QCM. If QRM wait min time (4) and wait time is added after acquiring
                    wait_time=int(wait_time)
                    if qblox_module.name not in self.readout_modules
                    else MIN_WAIT,  # TODO: add time of flight
                )
            )
            if qblox_module.name in self.readout_modules:
                self._append_acquire_instruction(
                    loop=bin_loop,
                    bin_index=bin_loop.counter_register,
                    acq_index=i,
                    sequencer=sequencer,  # type: ignore
                    weight_regs=weight_registers,
                    wait=wait_time - MIN_WAIT if (i < len(timeline) - 1) else MIN_WAIT,
                )

            # Add long wait for wait time if necessary
            if long_wait_time != 0:
                bin_loop.append_component(long_wait(long_wait_time))

        if self.repetition_duration is not None:
            wait_time = self.repetition_duration - bin_loop.duration_iter
            if wait_time > qblox_module._MIN_WAIT_TIME:  # pylint: disable=protected-access
                bin_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access
        return program

    def _generate_weights(self, sequencer: AWGQbloxADCSequencer) -> Weights:  # type: ignore
        """Generate acquisition weights.

        Returns:
            Weights: Acquisition weights.
        """
        weights = Weights()

        if self._get_instrument_from_sequencer(sequencer).name in self.control_modules:
            return weights
        pair = ([float(w) for w in sequencer.weights_i], [float(w) for w in sequencer.weights_q])
        weights.add_pair(pair=pair, indices=(0, 1))
        return weights

    def _append_acquire_instruction(
        self,
        loop: Loop,
        bin_index: Register | int,
        acq_index: int,
        sequencer: AWGQbloxADCSequencer,
        weight_regs: tuple[Register, Register],
        wait: int,
    ):
        """Append an acquire instruction to the loop."""
        weighed_acq = sequencer.weighed_acq_enabled

        acq_instruction = (
            AcquireWeighed(
                acq_index=acq_index,
                bin_index=bin_index,
                weight_index_0=weight_regs[0],
                weight_index_1=weight_regs[1],
                wait_time=wait,
            )
            if weighed_acq
            else Acquire(
                acq_index=acq_index,
                bin_index=bin_index,
                wait_time=wait,
            )
        )
        # TODO: implement time of flight properly to remove this hack
        loop.append_component(Wait(wait_time=220))
        loop.append_component(acq_instruction)

    def _init_weights_registers(self, registers: tuple[Register, Register], program: Program):
        """Initialize the weights `registers` and place the required instructions in the setup block of the `program`."""
        move_0 = Move(0, registers[0])
        move_1 = Move(1, registers[1])
        setup_block = program.get_block(name="setup")
        setup_block.append_components([move_0, move_1], bot_position=1)

    def get_sequencer_schedule(
        self, pulse_schedule: PulseSchedule, qblox_instruments: list[QbloxModule]
    ) -> tuple[list[tuple[AWGQbloxSequencer, PulseBusSchedule]], list[tuple[AWGQbloxSequencer, PulseBusSchedule]]]:
        """This method returns a dictionary containing the pulse schedule to be sent to each sequencer.
        This corresponds to a PulseBusSchedule object. Note that for multiplexed QRM more than one PulseBusSchedule is sent to the same
        bus (feedline) but to different sequencers (as qubit schedules), which is why QRM and QCM pulses are handled asymetrically
        in the methods below - and also why it is not possible to just group QRM and QCM pulses together under a single dictionary.

        Args:
            pulse_schedule (PulseSchedule): pulse schedule to be executed
            qblox_instruments (list[QbloxModule]): list of connected qblox modules

        Raises:
            ValueError: raises an error if readoud pulses are targeted at more tan one port

        Returns:
            dict[AWGQbloxSequencer, PulseBusSchedule]: dictionary of the pulse schedule (dict value) corresponding to a
            given sequencer (dict key)
        """
        qrm_sequencers = [
            sequencer
            for instrument in qblox_instruments
            for sequencer in instrument.awg_sequencers
            if instrument.name in self.readout_modules
        ]
        feedline_ports = {sequencer.chip_port_id for sequencer in qrm_sequencers}
        qcm_sequencers = [
            sequencer
            for instrument in qblox_instruments
            for sequencer in instrument.awg_sequencers
            if instrument.name in self.control_modules
        ]

        control_pulses = [
            pulse_bus_schedule
            for pulse_bus_schedule in pulse_schedule.elements
            if pulse_bus_schedule.port not in feedline_ports
        ]
        readout_pulses = [
            pulse_bus_schedule
            for pulse_bus_schedule in pulse_schedule.elements
            if pulse_bus_schedule.port in feedline_ports
        ]

        qcm_bus_schedules = [
            (sequencer, schedule)
            for sequencer in qcm_sequencers
            for schedule in control_pulses
            if sequencer.chip_port_id == schedule.port
        ]

        # Readout pulses should all be in one bus pulse schedule since they are all in the same line (feedline_input), so we separate them qubit-wise
        qrm_bus_schedules = [
            (sequencer, qubit_schedule)
            for sequencer in qrm_sequencers
            for schedule in readout_pulses
            for qubit_schedule in schedule.qubit_schedules()
            if sequencer.qubit == qubit_schedule.qubit
        ]
        return qrm_bus_schedules, qcm_bus_schedules

    def _get_instrument_from_sequencer(self, sequencer: AWGQbloxSequencer) -> QbloxModule:
        """Get the qblox module to which a given sequencer belongs

        Args:
            sequencer (AWGQbloxSequencer): qblox sequencer

        Returns:
            QbloxModule: qblox module
        """
        return next(
            instrument for instrument in self.qblox_modules for seq in instrument.awg_sequencers if seq == sequencer
        )
