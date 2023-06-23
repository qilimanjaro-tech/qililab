import numpy as np
import qblox_instruments.native.generic_func as gf
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qcodes import Instrument
from qililab.drivers import AWG
from qililab.config import logger
from qililab.pulse import PulseBusSchedule, PulseShape
from qpysequence.library import long_wait
from qpysequence.program import Block, Loop, Program, Register
from qpysequence.program.instructions import Play, ResetPh, SetAwgGain, SetPh, Stop
from qpysequence.sequence import Sequence as QpySequence
from qpysequence.utils.constants import AWG_MAX_GAIN
from qpysequence.waveforms import Waveforms
from typing import Any


class AWGSequencer(Sequencer, AWG):
    """Qililab's driver for QBlox-instruments Sequencer"""

    def __init__(
        self, parent: Instrument, name: str, seq_idx: int, output_i: int | None = None, output_q: int | None = None
    ):
        """Initialise the instrument.
        Args:
            parent (Instrument): Parent for the sequencer instance.
            name (str): Sequencer name
            seq_idx (int): sequencer identifier index
            output_i (int): output for i signal
            output_q (int): output for q signal
        """
        super().__init__(parent=parent, name=name, seq_idx=seq_idx)
        self.output_i = output_i
        self.output_q = output_q
        self._map_outputs()

    def _map_outputs(self):
        """Map sequencer paths with output channels."""
        if self.output_i is not None:
            self.set(f"channel_map_path{self.path_i}_out{self.output_i}_en", True)
        if self.output_q is not None:
            self.set(f"channel_map_path{self.path_q}_out{self.output_q}_en", True)

    def execute(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, num_bins: int):
        """Execute a PulseBusSchedule on the instrument.
        Args:
            pulse_bus_schedule (PulseBusSchedule): PulseBusSchedule to be translated into QASM program and executed.
            nshots (int): number of shots / hardware average
            repetition_duration (int): repetition duration
            num_bins (int): number of bins
        """
        self.nshots = nshots
        self.repetition_duration = repetition_duration
        self.num_bins = num_bins
        self.sequence = self._compile(pulse_bus_schedule)
        gf.arm_sequencer(sequencer=self.seq_idx)
        gf.start_sequencer(sequencer=self.seq_idx)

    def _translate_pulse_bus_schedule(self, pulse_bus_schedule: PulseBusSchedule):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule)
        program = self._generate_program(pulse_bus_schedule=pulse_bus_schedule, waveforms=waveforms)

        return QpySequence(program=program, waveforms=waveforms)

    def _compile(self, pulse_bus_schedule: PulseBusSchedule) -> QpySequence:
        """Compiles the ``PulseBusSchedule`` into an assembly program.

        Args:
            pulse_bus_schedule (PulseBusSchedule): the list of pulses to be converted into a program
        """
        sequence = self._translate_pulse_bus_schedule(pulse_bus_schedule=pulse_bus_schedule)

        return sequence

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
                if (self.path_i, self.path_q) == (1, 0):
                    pair = pair[::-1]  # swap paths
                waveforms.add_pair(pair=pair, name=pulse_event.pulse.label())

        return waveforms

    def _generate_program(self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms):
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
        self._append_acquire_instruction(loop=bin_loop, bin_index=bin_loop.counter_register, sequencer_id=self.seq_idx)
        if self.repetition_duration is not None:
            wait_time = self.repetition_duration - bin_loop.duration_iter
            if wait_time > self._MIN_WAIT_TIME:
                bin_loop.append_component(long_wait(wait_time=wait_time))

        logger.info("Q1ASM program: \n %s", repr(program))  # pylint: disable=protected-access

        return program
