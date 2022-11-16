"""Qblox module class"""
import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from qpysequence.acquisitions import Acquisitions
from qpysequence.library import long_wait, set_awg_gain_relative, set_phase_rad
from qpysequence.program import Block, Loop, Program, Register
from qpysequence.program.instructions import Play, Stop, Wait
from qpysequence.sequence import Sequence
from qpysequence.waveforms import Waveforms

from qililab.instruments.awg import AWG
from qililab.instruments.instrument import Instrument
from qililab.pulse import PulseBusSchedule, PulseShape
from qililab.typings.instruments import Pulsar, QcmQrm


class QbloxModule(AWG):
    """Qblox Module class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    _MAX_BINS: int = 131072
    _NUM_SEQUENCERS: int = 4
    _MIN_WAIT_TIME: int = 4  # in ns

    @dataclass
    class QbloxModuleSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
            sequencer (int): Index of the sequencer to use.
            sync_enabled (bool): Enable synchronization over multiple instruments.
        """

        sync_enabled: bool
        num_bins: int

    settings: QbloxModuleSettings
    device: Pulsar | QcmQrm
    # Cache containing the last PulseSequence, nshots and repetition_duration used.
    _cache: Tuple[PulseBusSchedule, int, int] | None = None

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        self._set_sync_enabled()
        self._map_outputs()
        self._set_nco()

    @property
    def module_type(self):
        """returns the qblox module type. Options: QCM or QRM"""
        return self.device.module_type()

    def run(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path):
        """Run execution of a pulse sequence.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse sequence.
        """
        self._check_cached_values(
            pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, path=path
        )
        self.start_sequencer()

    def _check_cached_values(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path
    ):
        """check if values are already cached and upload if not cached"""
        if (pulse_bus_schedule, nshots, repetition_duration) != self._cache:
            self._cache = (pulse_bus_schedule, nshots, repetition_duration)
            sequence = self._translate_pulse_bus_schedule(
                pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration
            )
            self.upload(sequence=sequence, path=path)

    def _translate_pulse_bus_schedule(
        self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int
    ):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_bus_schedule (PulseBusSchedule): Pulse bus schedule to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulse_bus_schedule=pulse_bus_schedule)
        acquisitions = self._generate_acquisitions()
        program = self._generate_program(
            pulse_bus_schedule=pulse_bus_schedule,
            waveforms=waveforms,
            nshots=nshots,
            repetition_duration=repetition_duration,
        )
        weights = self._generate_weights()
        return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)

    def _generate_program(
        self, pulse_bus_schedule: PulseBusSchedule, waveforms: Waveforms, nshots: int, repetition_duration: int
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
        bin_loop = Loop(name="binning", begin=0, end=int(self.num_bins))
        avg_loop = Loop(name="average", begin=0, end=nshots)
        bin_loop.append_block(block=avg_loop, bot_position=1)
        stop = Block(name="stop")
        stop.append_component(Stop())
        program.append_block(block=bin_loop)
        program.append_block(block=stop)
        timeline = pulse_bus_schedule.timeline
        if timeline[0].start != 0:  # TODO: Make sure that start time of Pulse is 0 or bigger than 4
            avg_loop.append_component(Wait(wait_time=int(timeline[0].start)))

        for i, pulse_event in enumerate(timeline):
            waveform_pair = waveforms.find_pair_by_name(pulse_event.pulse.label())
            wait_time = timeline[i + 1].start - pulse_event.start if (i < (len(timeline) - 1)) else self.final_wait_time
            avg_loop.append_component(set_phase_rad(rads=pulse_event.pulse.phase))
            avg_loop.append_component(
                set_awg_gain_relative(gain_0=pulse_event.pulse.amplitude, gain_1=pulse_event.pulse.amplitude)
            )
            avg_loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=int(wait_time),
                )
            )
        self._append_acquire_instruction(loop=avg_loop, register=avg_loop.counter_register)
        avg_loop.append_block(long_wait(wait_time=repetition_duration - avg_loop.duration_iter), bot_position=1)
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

    def _append_acquire_instruction(self, loop: Loop, register: Register):
        """Append an acquire instruction to the loop."""

    def start_sequencer(self):
        """Start sequencer and execute the uploaded instructions."""
        for seq_idx in range(self.num_sequencers):
            self.device.arm_sequencer(sequencer=seq_idx)
            self.device.start_sequencer(sequencer=seq_idx)

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._set_nco()
        self._set_gains()
        self._set_offsets()

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        for seq_idx in range(self.num_sequencers):
            self.device.stop_sequencer(sequencer=seq_idx)

    def clear_cache(self):
        """Empty cache."""
        self._cache = None

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument."""
        self.clear_cache()
        self.device.reset()

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
