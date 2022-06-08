"""Qblox pulsar class"""

import itertools
import json
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

from qililab.config import logger
from qililab.instruments.awg import AWG
from qililab.pulse import Pulse, PulseSequence, PulseShape
from qililab.typings import Pulsar, ReferenceClock
from qililab.utils import nested_dataclass


class QbloxPulsar(AWG):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    MAX_BINS = 131072

    @nested_dataclass
    class QbloxPulsarSettings(AWG.AWGSettings):
        """Contains the settings of a specific pulsar.

        Args:
            reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
            sequencer (int): Index of the sequencer to use.
            sync_enabled (bool): Enable synchronization over multiple instruments.
            gain (float): Gain step used by the sequencer.
        """

        reference_clock: ReferenceClock
        sequencer: int
        sync_enabled: bool
        gain: float

    device: Pulsar
    settings: QbloxPulsarSettings
    # Cache containing the last PulseSequence, nshots and repetition_duration used.
    _cache: Tuple[PulseSequence, int, int] | None

    def __init__(self):
        super().__init__()
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
                pulses=pulse_sequence.pulses, nshots=nshots, repetition_duration=repetition_duration
            )
            self.upload(sequence=sequence, path=path)

        self.start()

    def _translate_pulse_sequence(self, pulses: List[Pulse], nshots: int, repetition_duration: int):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms = self._generate_waveforms(pulses=pulses)
        acquisitions = self._generate_acquisitions()
        program = self._generate_program(
            pulses=pulses, waveforms=waveforms, nshots=nshots, repetition_duration=repetition_duration
        )
        weights = self._generate_weights()
        return Sequence(program=program, waveforms=waveforms, acquisitions=acquisitions, weights=weights)

    def _generate_program(self, pulses: List[Pulse], waveforms: Waveforms, nshots: int, repetition_duration: int):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
            waveforms (Waveforms): Waveforms.

        Returns:
            Program: Q1ASM program.
        """
        program = Program()
        loop = Loop(name="loop", iterations=nshots)
        stop = Block(name="stop")
        stop.append_component(Stop())
        # TODO: Make sure that start time of Pulse is 0 or bigger than 4
        if pulses[0].start != 0:
            loop.append_component(Wait(wait_time=pulses[0].start))

        for i, pulse in enumerate(pulses):
            waveform_pair = waveforms.find_pair_by_name(str(pulse))
            wait_time = pulses[i + 1].start - pulse.start if (i < (len(pulses) - 1)) else self.final_wait_time
            loop.append_component(set_phase_rad(rads=pulse.phase))
            loop.append_component(set_awg_gain_relative(gain_0=pulse.amplitude, gain_1=pulse.amplitude))
            loop.append_component(
                Play(
                    waveform_0=waveform_pair.waveform_i.index,
                    waveform_1=waveform_pair.waveform_q.index,
                    wait_time=wait_time,
                )
            )

        self._append_acquire_instruction(loop=loop)

        loop.append_component(long_wait(wait_time=repetition_duration - loop.duration_iter))
        program.append_block(block=loop)
        program.append_block(block=stop)
        return program

    def _generate_acquisitions(self) -> Acquisitions:
        """Generate Acquisitions object.

        Returns:
            Acquisitions: Acquisitions object.
        """
        return Acquisitions()

    def _generate_weights(self) -> dict:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return {}

    def _append_acquire_instruction(self, loop: Loop):
        """Append an acquire instruction to the loop."""

    @AWG.CheckConnected
    def start(self):
        """Execute the uploaded instructions."""
        self.device.arm_sequencer()
        self.device.start_sequencer()

    @AWG.CheckConnected
    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._set_gain()
        self._set_offsets()

    @AWG.CheckConnected
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        self.device.stop_sequencer()

    @AWG.CheckConnected
    def close(self):
        """Empty cache and close connection with the instrument."""
        self._cache = None
        super().close()

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
        self._set_nco()

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
        getattr(self.device, f"sequencer{self.sequencer}").sequence(file_path)

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path0(self.gain)
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path1(self.gain)

    def _set_offsets(self):
        """Set I and Q offsets of sequencer."""
        getattr(self.device, f"sequencer{self.sequencer}").offset_awg_path0(self.offset_i)
        getattr(self.device, f"sequencer{self.sequencer}").offset_awg_path1(self.offset_q)

    def _set_nco(self):
        """Enable modulation of pulses and setup NCO frequency."""
        getattr(self.device, f"sequencer{self.sequencer}").mod_en_awg(True)
        getattr(self.device, f"sequencer{self.sequencer}").nco_freq(self.frequency)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.reference_clock.value)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        getattr(self.device, f"sequencer{self.sequencer}").sync_en(self.sync_enabled)

    def _map_outputs(self):
        """Disable all connections and map sequencer paths with output channels."""
        # Disable all connections
        for sequencer, out in itertools.product(self.device.sequencers, range(4)):
            if hasattr(sequencer, f"channel_map_path{out % 2}_out{out}_en"):
                sequencer.set(f"channel_map_path{out % 2}_out{out}_en", False)
        getattr(self.device, f"sequencer{self.sequencer}").channel_map_path0_out0_en(True)
        getattr(self.device, f"sequencer{self.sequencer}").channel_map_path1_out1_en(True)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        self.device = Pulsar(name=f"{self.name.value}_{self.id_}", identifier=self.ip)

    def _generate_waveforms(self, pulses: List[Pulse]):
        """Generate I and Q waveforms from a PulseSequence object.

        Args:
            pulse_sequence (PulseSequence): PulseSequence object.

        Returns:
            Waveforms: Waveforms object containing the generated waveforms.
        """
        waveforms = Waveforms()

        unique_pulses: List[Tuple[int, PulseShape]] = []

        for pulse in pulses:
            if (pulse.duration, pulse.pulse_shape) not in unique_pulses:
                unique_pulses.append((pulse.duration, pulse.pulse_shape))
                envelope = pulse.envelope(amplitude=1)
                real = np.real(envelope) + self.offset_i
                imag = np.imag(envelope) + self.offset_q
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
    def sequencer(self):
        """QbloxPulsar 'sequencer' property.

        Returns:
            int: settings.sequencer.
        """
        return self.settings.sequencer

    @property
    def sync_enabled(self):
        """QbloxPulsar 'sync_enabled' property.

        Returns:
            bool: settings.sync_enabled.
        """
        return self.settings.sync_enabled

    @property
    def gain(self):
        """QbloxPulsar 'gain' property.

        Returns:
            float: settings.gain.
        """
        return self.settings.gain

    @property
    def offset_i(self):
        """QbloxPulsar 'offset_i' property.

        Returns:
            float: settings.offset_i
        """
        return self.settings.offset_i

    @property
    def offset_q(self):
        """QbloxPulsar 'offset_q' property.

        Returns:
            float: settings.offset_q.
        """
        return self.settings.offset_q

    @property
    def epsilon(self):
        """QbloxPulsar 'epsilon' property.

        Returns:
            float: settings.epsilon.
        """
        return self.settings.epsilon

    @property
    def delta(self):
        """QbloxPulsar 'delta' property.

        Returns:
            float: settings.delta.
        """
        return self.settings.delta

    @property
    def final_wait_time(self) -> int:
        """QbloxPulsar 'final_wait_time' property.

        Returns:
            int: Final wait time.
        """
        return 4
