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

from qililab.pulse import PulseSchedule

import numpy as np
from qpysequence import Acquisitions, Program
from qpysequence import Sequence as QpySequence
from qpysequence import Waveforms, Weights
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Register
from qpysequence.program.instructions import Play, ResetPh, SetAwgGain, SetPh, Stop
from qpysequence.utils.constants import AWG_MAX_GAIN


class QbloxCompiler():
    def __init__(self, pulse_schedule: PulseSchedule, platform):
        self.buses = platform.buses
        self.pulse_schedule = pulse_schedule
        
    def clear_cache(self):
        """Empty cache."""
        self._cache = {}
        self.sequences = {}
    
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
                sequence = self._translate_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule, sequencer=sequencer)
                compiled_sequences.append(sequence)
                self._cache[sequencer.identifier] = pulse_bus_schedule
                self.sequences[sequencer.identifier] = (sequence, False)
            else:
                compiled_sequences.append(self.sequences[sequencer.identifier][0])
        return compiled_sequences
    
    def _generate_program(self, waveforms: Waveforms, sequencer: int):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): pulse sequence
            waveforms (Waveforms): waveforms
            sequencer (int): index of the sequencer to generate the program

        Returns:
            Program: Q1ASM program.
        """
        programs = {schedule.port: {"program": Program(),
                                    "start": Block(name=f"start_{schedule.port}"),
                                    "average": Loop(name="average", begin=int(self.nshots)),
                                    "bin": Loop(name="bin", begin=0, end=self.num_bins, step=1)} for schedule in self.pulse_schedule.elements}
        
        
            
            
            
            
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
    
    
