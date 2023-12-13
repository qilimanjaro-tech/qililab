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

from qililab.pulse import PulseSchedule, PulseBusSchedule, PulseShape
from qpysequence.program.instructions import Play, ResetPh, SetAwgGain, SetPh, Stop


import numpy as np
from qpysequence import Acquisitions, Program
from qpysequence import Sequence as QpySequence
from qpysequence import Waveforms, Weights
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Register
from qpysequence.utils.constants import AWG_MAX_GAIN
from qpysequence.program.instructions import Acquire, AcquireWeighed, Move

from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.qblox import QbloxModule, QbloxQCM, QbloxQRM

from qililab.config import logger




class QbloxCompiler():
    def __init__(self, platform):
        self.qblox_modules = [instrument for instrument in platform.instruments.elements if isinstance(instrument, QbloxModule)]
        self.buses = platform.buses
        # init variables as empty
        self.nshots = None
        self.num_bins = None
        self.repetition_duration = None
        if not any(isinstance(qblox, QbloxQRM) for qblox in self.qblox_modules): # Raise error if qrm is not found
            raise ValueError(f"At least one QRM should be connected. Found {sum(isinstance(qblox, QbloxQRM) for qblox in self.qblox_modules)} QRM modules")
        
    # TODO: add comments
    def compile(self, pulse_schedule: PulseSchedule, num_avg: int, repetition_duration: int, num_bins: int):
        
        if num_avg != self.nshots or repetition_duration != self.repetition_duration or num_bins != self.num_bins:
            self.nshots = num_avg
            self.repetition_duration = repetition_duration
            self.num_bins = num_bins
            for qblox_module in self.qblox_modules:
                qblox_module.clear_sequence_cache()

        sequencer_qrm_bus_schedules, sequencer_qcm_bus_schedules = self.get_pulse_bus_schedule_sequencers(pulse_schedule, self.qblox_modules)

        compiled_sequences = {}
        
        for sequencer, bus_schedule in sequencer_qrm_bus_schedules + sequencer_qcm_bus_schedules:
            qblox_module = self._get_instrument_from_sequencer(sequencer)
            if bus_schedule == qblox_module.cache.get(sequencer.identifier): # if it's already cached then dont compile
                compiled_sequences[self.buses.get(bus_schedule.port).alias] = qblox_module.sequences[sequencer.identifier][0] #TODO: why the 0 index
            else:
                compiled_sequences[self.buses.get(bus_schedule.port).alias] = self._translate_pulse_bus_schedule(bus_schedule, sequencer)
                qblox_module.cache[sequencer.identifier] = bus_schedule
        
        qrm = next((qblox_module for qblox_module in self.qblox_modules if qblox_module.module_type == "QRM")) # FIXME: only one qrm supported
        missing_seq_ids = [cached_seq_id for cached_seq_id in qrm.sequences.keys() if cached_seq_id not in (sequencer for sequencer, _ in sequencer_qrm_bus_schedules)]
        for seq_id in missing_seq_ids:
            _ = qrm.sequences.pop(seq_id)
            _ = qrm.cache.pop(seq_id)
            
        return compiled_sequences


    def _translate_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule, sequencer: AWGQbloxSequencer):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.
            sequencer (int): index of the sequencer to generate the program

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule, sequencer=sequencer)
        acquisitions = self._generate_acquisitions(sequencer)
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms, sequencer=sequencer
        )
        weights = self._generate_weights(sequencer=sequencer)
        return QpySequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)
    

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
    
    def _generate_acquisitions(self, sequencer: AWGQbloxSequencer) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "default", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        # FIXME: is it really necessary to generate acquisitions for a QCM??
        acquisitions = Acquisitions()
        if self._get_instrument_from_sequencer(sequencer).module_type == "QCM":
            return acquisitions
        acquisitions.add(name="default", num_bins=self.num_bins, index=0)
        return acquisitions
    
    
    def _generate_program(  # pylint: disable=too-many-locals
        self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms, sequencer: AWGQbloxSequencer
    ):
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
        
        # Define program's blocks
        program = Program()
        start = Block(name="start")
        start.append_component(ResetPh())
        program.append_block(block=start)
        # Create registers with 0 and 1 (necessary for qblox)
        weight_registers = Register(), Register()
        if qblox_module.module_type == "QRM":
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
        if qblox_module.module_type == "QRM":
            self._append_acquire_instruction(
                loop=bin_loop, bin_index=bin_loop.counter_register, sequencer=sequencer, weight_regs=weight_registers
            )
        if self.repetition_duration is not None:
            wait_time = self.repetition_duration - bin_loop.duration_iter
            if wait_time > qblox_module._MIN_WAIT_TIME:
                bin_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access
        return program
    
    
    def _generate_weights(self, sequencer: AWGQbloxSequencer) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        weights = Weights()

        if self._get_instrument_from_sequencer(sequencer).module_type == "QCM":
            return weights
        pair = ([float(w) for w in sequencer.weights_i], [float(w) for w in sequencer.weights_q])
        if (sequencer.path_i, sequencer.path_q) == (1, 0):
            pair = pair[::-1]  # swap paths
        weights.add_pair(pair=pair, indices=(0, 1))
        return weights 
        
    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, sequencer: AWGQbloxSequencer, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""
        weighed_acq = sequencer.weighed_acq_enabled
        qblox_module = self._get_instrument_from_sequencer(sequencer)

        acq_instruction = (
            AcquireWeighed(
                acq_index=0,
                bin_index=bin_index,
                weight_index_0=weight_regs[0],
                weight_index_1=weight_regs[1],
                wait_time=qblox_module._MIN_WAIT_TIME,
            )
            if weighed_acq
            else Acquire(acq_index=0, bin_index=bin_index, wait_time=qblox_module._MIN_WAIT_TIME)
        )
        loop.append_component(acq_instruction)

    def _init_weights_registers(self, registers: tuple[Register, Register], values: tuple[int, int], program: Program): #TODO: is values used anywhere?
        """Initialize the weights `registers` to the `values` specified and place the required instructions in the
        setup block of the `program`."""
        move_0 = Move(0, registers[0])
        move_1 = Move(1, registers[1])
        setup_block = program.get_block(name="setup")
        setup_block.append_components([move_0, move_1], bot_position=1)


    
    def get_pulse_bus_schedule_sequencers(self, pulse_schedule: PulseSchedule, qblox_instruments: list[QbloxModule]) -> dict[AWGQbloxSequencer, PulseBusSchedule]:
        qrm_sequencers = [sequencer for instrument in qblox_instruments for sequencer in instrument.awg_sequencers if instrument.module_type == "QRM"]
        feedline_port = qrm_sequencers[0].chip_port_id #FIXME: only one chip port id supported for qrm
        qcm_sequencers = [sequencer for instrument in qblox_instruments for sequencer in instrument.awg_sequencers if instrument.module_type == "QCM"]
        
        control_pulses = [pulse for pulse in pulse_schedule.elements if pulse.port != feedline_port]
        readout_pulses = [pulse for pulse in pulse_schedule.elements if pulse.port == feedline_port]
        
        qcm_bus_schedules = [(sequencer, schedule) for sequencer in qcm_sequencers for schedule in control_pulses if sequencer.chip_port_id == schedule.port]
        if len(readout_pulses) > 1:
            raise ValueError(f"readout pulses targeted at more than one port. Expected only one target port and instead got {len(readout_pulses)}")
        # Readout pulses should all be in one bus pulse schedule since they are all in the same line (feedline_input)
        qrm_bus_schedules = [(sequencer, schedule) for sequencer in qrm_sequencers for schedule in readout_pulses[0].qubit_schedules() if sequencer.qubit == schedule.qubit]
        return qrm_bus_schedules, qcm_bus_schedules
    
    def _get_instrument_from_sequencer(self, sequencer) -> QbloxModule:
        return next(instrument for instrument in self.qblox_modules for seq in instrument.awg_sequencers if seq == sequencer)