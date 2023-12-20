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
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qpysequence.acquisitions import Acquisitions
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Program, Register
from qpysequence.program.instructions import Play, ResetPh, SetAwgGain, SetPh, Stop
from qpysequence.sequence import Sequence as QpySequence
from qpysequence.utils.constants import AWG_MAX_GAIN
from qpysequence.waveforms import Waveforms
from qpysequence.weights import Weights

from qililab.config import logger
from qililab.drivers.instruments.instrument_driver_factory import InstrumentDriverFactory
from qililab.drivers.interfaces import AWG
from qililab.pulse import PulseBusSchedule, PulseShape


@InstrumentDriverFactory.register
class SequencerQCM(Sequencer, AWG):
    """Qililab's driver for QBlox-instruments Sequencer

    Args:
        parent (Instrument): Parent for the sequencer instance.
        name (str): Sequencer name
        seq_idx (int): sequencer identifier index
    """

    _MIN_WAIT_TIME: int = 4

    @property
    def params(self):
        """return the parameters of the instrument"""
        return self.parameters

    @property
    def alias(self):
        """return the alias of the instrument, which corresponds to the QCodes name attribute"""
        return self.name

    def execute(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int):
        """Execute a PulseBusSchedule on the instrument.

        Args:
            pulse_bus_schedule (PulseBusSchedule): PulseBusSchedule to be translated into QASM program and executed.
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins
        """
        sequence = self._translate_pulse_bus_schedule(pulse_bus_schedule, nshots, repetition_duration, num_bins)
        self.set("sequence", sequence.todict())
        self.parent.arm_sequencer(sequencer=self.seq_idx)
        self.parent.start_sequencer(sequencer=self.seq_idx)

    def _translate_pulse_bus_schedule(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int
    ):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule)
        acquisitions = self._generate_acquisitions(num_bins=num_bins)
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule,
            waveforms=waveforms,
            nshots=nshots,
            repetition_duration=repetition_duration,
            num_bins=num_bins,
        )
        weights = self._generate_weights()

        return QpySequence(program=program, waveforms=waveforms, weights=weights, acquisitions=acquisitions)

    def _generate_weights(self) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return Weights()

    def _generate_acquisitions(self, num_bins: int) -> Acquisitions:  # pylint: disable=unused-argument
        """Generate Acquisitions object.

        Args:
            num_bins (int): number of bins

        Returns:
            Acquisitions: Acquisitions object.
        """
        return Acquisitions()

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

    def _init_weights_registers(self, registers: tuple[Register, Register], values: tuple[int, int], program: Program):
        """Initialize the weights `registers` to the `values` specified and place the required instructions in the
        setup block of the `program`."""

    def _append_acquire_instruction(
        self, loop: Loop, bin_index: Register | int, weight_regs: tuple[Register, Register]
    ):
        """Append an acquire instruction to the loop."""

    def _generate_program(  # pylint: disable=too-many-locals
        self,
        pulse_bus_schedule: PulseBusSchedule,
        waveforms: Waveforms,
        nshots: int,
        repetition_duration: int,
        num_bins: int,
    ):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): pulse sequence
            waveforms (Waveforms): waveforms
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins

        Returns:
            Program: Q1ASM program.
        """
        # Define program's blocks
        program = Program()
        # Create registers with 0 and 1 (necessary for qblox)
        weight_registers = Register(), Register()
        self._init_weights_registers(registers=weight_registers, values=(0, 1), program=program)
        avg_loop = Loop(name="average", begin=nshots)
        bin_loop = Loop(name="bin", begin=0, end=num_bins, step=1)
        avg_loop.append_component(bin_loop)
        program.append_block(avg_loop)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=stop)
        timeline = pulse_bus_schedule.timeline
        if len(timeline) > 0 and timeline[0].start_time != 0:
            bin_loop.append_component(long_wait(wait_time=int(timeline[0].start_time)))

        for i, pulse_event in enumerate(timeline):
            print("Pulse label: ", pulse_event.pulse.label())
            waveform_pair = waveforms.find_pair_by_name(pulse_event.pulse.label())
            wait_time = timeline[i + 1].start_time - pulse_event.start_time if (i < (len(timeline) - 1)) else 4
            bin_loop.append_component(ResetPh())
            gain = int(np.abs(pulse_event.pulse.amplitude) * AWG_MAX_GAIN)  # np.abs() needed for negative pulses
            bin_loop.append_component(SetAwgGain(gain_0=gain, gain_1=gain))
            phase = int((pulse_event.pulse.phase % (2 * np.pi)) * 1e9 / (2 * np.pi))
            bin_loop.append_component(SetPh(phase=phase))
            bin_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=int(wait_time),
                )
            )
        self._append_acquire_instruction(
            loop=bin_loop, bin_index=bin_loop.counter_register, weight_regs=weight_registers
        )
        if repetition_duration is not None:
            wait_time = repetition_duration - bin_loop.duration_iter
            if wait_time > self._MIN_WAIT_TIME:
                bin_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access

        return program
