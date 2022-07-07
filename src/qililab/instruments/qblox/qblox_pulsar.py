"""Qblox pulsar class"""
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from qpysequence.acquisitions import Acquisitions
from qpysequence.block import Block
from qpysequence.instructions.control import Stop
from qpysequence.instructions.real_time import Play, Wait
from qpysequence.library import long_wait, set_awg_gain_relative, set_phase_rad
from qpysequence.loop import Loop
from qpysequence.program import Program
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments.awg import AWG
from qililab.pulse import Pulse, PulseSequence, PulseShape
from qililab.typings import Pulsar, ReferenceClock


class QbloxPulsar(AWG):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    _MAX_BINS: int = 131072
    _NUM_SEQUENCERS: int = 4
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxPulsarSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
            sequencer (int): Index of the sequencer to use.
            sync_enabled (bool): Enable synchronization over multiple instruments.
        """

        reference_clock: ReferenceClock
        sync_enabled: bool
        num_bins: int

    settings: QbloxPulsarSettings
    device: Pulsar
    # Cache containing the last PulseSequence, nshots and repetition_duration used.
    _cache: Tuple[PulseSequence, int, int] | None

    def __init__(self, settings: dict):
        super().__init__(settings=settings)
        self._cache = None

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        super().connect()
        self.initial_setup()

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """
        if (pulse_sequence, nshots, repetition_duration) != self._cache:
            self._cache = (pulse_sequence, nshots, repetition_duration)
            sequence = self._translate_pulse_sequence(
                pulse_sequence=pulse_sequence, nshots=nshots, repetition_duration=repetition_duration
            )
            self.upload(sequence=sequence, path=path)

        self.start_sequencer()

    def _translate_pulse_sequence(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_sequence=pulse_sequence)
        acquisitions = self._generate_acquisitions()
        program = self._generate_program(
            pulse_sequence=pulse_sequence, waveforms=waveforms, nshots=nshots, repetition_duration=repetition_duration
        )
        weights = self._generate_weights()
        return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)

    def _generate_program(
        self, pulse_sequence: PulseSequence, waveforms: Waveforms, nshots: int, repetition_duration: int
    ):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
            waveforms (Waveforms): Waveforms.

        Returns:
            Program: Q1ASM program.
        """
        # Define program's blocks
        program = Program()
        bin_loop = Loop(name="binning", iterations=int(self.num_bins))
        avg_loop = Loop(name="average", iterations=nshots)
        bin_loop.append_block(block=avg_loop, bot_position=1)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=bin_loop)
        program.append_block(block=stop)
        pulses = pulse_sequence.pulses
        if pulses[0].start != 0:  # TODO: Make sure that start time of Pulse is 0 or bigger than 4
            avg_loop.append_component(Wait(wait_time=int(pulses[0].start)))

        for i, pulse in enumerate(pulses):
            waveform_pair = waveforms.find_pair_by_name(str(pulse))
            wait_time = pulses[i + 1].start - pulse.start if (i < (len(pulses) - 1)) else self.final_wait_time
            avg_loop.append_component(set_phase_rad(rads=pulse.phase))
            avg_loop.append_component(set_awg_gain_relative(gain_0=pulse.amplitude, gain_1=pulse.amplitude))
            avg_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=int(wait_time),
                )
            )
        self._append_acquire_instruction(loop=avg_loop, register="TR10")
        avg_loop.append_block(long_wait(wait_time=repetition_duration - avg_loop.duration_iter), bot_position=1)
        avg_loop.replace_register(old="TR10", new=bin_loop.counter_register)
        avg_loop.replace_register(old="TR0", new="R2")  # FIXME: Qpysequence: Automatic reallocation doesn't work
        return program

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object, currently containing a single acquisition named "single", with num_bins = 1
        and index = 0.

        Returns:
            Acquisitions: Acquisitions object.
        """
        acquisitions = Acquisitions()
        acquisitions.add(name="single", num_bins=1, index=0)
        acquisitions.add(name="binning", num_bins=int(self.num_bins) + 1, index=1)  # binned acquisition
        return acquisitions

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

    def _append_acquire_instruction(self, loop: Loop, register: str):
        """Append an acquire instruction to the loop."""

    @AWG.CheckConnected
    def start_sequencer(self):
        """Start sequencer and execute the uploaded instructions."""
        self.device.arm_sequencer()
        self.device.start_sequencer()

    @AWG.CheckConnected
    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._set_nco()
        self._set_gains()
        self._set_offsets()

    @AWG.CheckConnected
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        self.device.stop_sequencer()

    @AWG.CheckConnected
    def close(self):
        """Empty cache and close connection with the instrument."""
        self._cache = None
        try:
            super().close()
        except ValueError:
            self._connected = False
            self.device.close()

    @AWG.CheckConnected
    def reset(self):
        """Reset instrument."""
        self.device.reset()

    @AWG.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        self.reset()
        self._set_reference_source()
        self._set_sync_enabled()
        self._map_outputs()

    @AWG.CheckConnected
    def upload(self, sequence: Sequence, path: Path):
        """Upload sequence to sequencer.

        Args:
            sequence (Sequence): Sequence object containing the waveforms, weights,
            acquisitions and program of the sequence.
        """
        file_path = str(path / f"{self.name.value}_sequence.yml")
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            json.dump(obj=sequence.todict(), fp=file)
        for seq_idx in range(self.num_sequencers):
            self.device.sequencers[seq_idx].sequence(file_path)

    def _set_gains(self):
        """Set gain of sequencer for all paths."""
        for seq_idx, gain in enumerate(self.gain):
            self.device.sequencers[seq_idx].gain_awg_path0(gain)
            self.device.sequencers[seq_idx].gain_awg_path1(gain)

    def _set_offsets(self):
        """Set I and Q offsets of sequencer."""
        for seq_idx, (offset_i, offset_q) in enumerate(zip(self.offset_i, self.offset_q)):
            self.device.sequencers[seq_idx].offset_awg_path0(offset_i)
            self.device.sequencers[seq_idx].offset_awg_path1(offset_q)

    def _set_nco(self):
        """Enable modulation of pulses and setup NCO frequency."""
        for seq_idx, frequency in enumerate(self.multiplexing_frequencies):
            self.device.sequencers[seq_idx].mod_en_awg(True)
            self.device.sequencers[seq_idx].nco_freq(frequency)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.reference_clock.value)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        for seq_idx in range(self.num_sequencers):
            self.device.sequencers[seq_idx].sync_en(self.sync_enabled)

    def _map_outputs(self):
        """Disable all connections and map sequencer paths with output channels."""
        # Disable all connections
        for sequencer, out in itertools.product(self.device.sequencers, range(self._NUM_SEQUENCERS)):
            if hasattr(sequencer, f"channel_map_path{out % 2}_out{out}_en"):
                sequencer.set(f"channel_map_path{out % 2}_out{out}_en", False)

        for seq_idx in range(self.num_sequencers):
            self.device.sequencers[seq_idx].channel_map_path0_out0_en(True)
            self.device.sequencers[seq_idx].channel_map_path1_out1_en(True)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        self.device = Pulsar(name=f"{self.name.value}_{self.id_}", identifier=self.ip)

    def _generate_waveforms(self, pulse_sequence: PulseSequence):
        """Generate I and Q waveforms from a PulseSequence object.

        Args:
            pulse_sequence (PulseSequence): PulseSequence object.

        Returns:
            Waveforms: Waveforms object containing the generated waveforms.
        """
        waveforms = Waveforms()

        unique_pulses: List[Tuple[int, PulseShape]] = []

        for pulse in pulse_sequence.pulses:
            if (pulse.duration, pulse.pulse_shape) not in unique_pulses:
                unique_pulses.append((pulse.duration, pulse.pulse_shape))
                envelope = pulse.envelope(amplitude=1)
                real = np.real(envelope)
                imag = np.imag(envelope)
                waveforms.add_pair((real, imag), name=str(pulse))

        return waveforms

    @property
    def reference_clock(self):
        """QbloxPulsar 'reference_clock' property.

        Returns:
            ReferenceClock: settings.reference_clock.
        """
        return self.settings.reference_clock

    @property
    def sync_enabled(self):
        """QbloxPulsar 'sync_enabled' property.

        Returns:
            bool: settings.sync_enabled.
        """
        return self.settings.sync_enabled

    @property
    def final_wait_time(self) -> int:
        """QbloxPulsar 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return self._MIN_WAIT_TIME

    @property
    def num_bins(self) -> int:
        """QbloxPulsar 'num_bins' property.

        Returns:
            int: Number of bins used.
        """
        return self.settings.num_bins
