"""Qblox pulsar class"""
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
from qpysequence.instructions import Acquire, Play, SetAwgGain, Wait
from qpysequence.library import long_wait, set_phase_rad
from qpysequence.loop import Loop
from qpysequence.program import Program
from qpysequence.sequence import Sequence

from qililab.instruments.qubit_instrument import QubitInstrument
from qililab.instruments.qubit_readout import QubitReadout
from qililab.pulse import Pulse
from qililab.typings import Pulsar, ReferenceClock
from qililab.utils import nested_dataclass


class QbloxPulsar(QubitInstrument):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    MAX_GAIN = 2**16 - 1

    @nested_dataclass
    class QbloxPulsarSettings(QubitInstrument.QubitInstrumentSettings):
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

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        super().connect()
        self.initial_setup()

    def run(self, pulses: List[Pulse]):
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.
        """
        sequence = self._translate_pulse_sequence(pulses=pulses)
        self.upload(sequence=sequence)
        self.start()

    def _translate_pulse_sequence(self, pulses: List[Pulse]):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms_dict = self._generate_waveforms(pulses=pulses)
        program = self._generate_program(pulses=pulses)
        return Sequence(program=program, waveforms=waveforms_dict, acquisitions={}, weights={})

    def _generate_program(self, pulses: List[Pulse]):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.

        Returns:
            Program: Q1ASM program.
        """
        program = Program()
        loop = Loop(name="loop", iterations=self.hardware_average)
        # TODO: Make sure that start time of Pulse is 0 or bigger than 4
        if pulses[0].start != 0:
            loop.append_component(Wait(wait_time=pulses[0].start))

        if isinstance(self, QubitReadout):
            final_wait_time = self.delay_before_readout
        else:
            final_wait_time = 4  # ns

        for i, pulse in enumerate(pulses):
            if i < len(pulses) - 1:
                wait_time = pulses[i + 1].start - pulse.start
            else:
                wait_time = final_wait_time
            loop.append_component(set_phase_rad(rads=pulse.phase))
            loop.append_component(
                SetAwgGain(gain_0=self.MAX_GAIN * pulse.amplitude, gain_1=self.MAX_GAIN * pulse.amplitude)
            )
            loop.append_component(Play(waveform_0=pulse.index, waveform_1=pulse.index + 1, wait_time=wait_time))

        if isinstance(self, QubitReadout):
            loop.append_component(Acquire(acq_index=0, bin_index=1, wait_time=4))

        loop.append_component(long_wait(wait_time=self.repetition_duration - loop.duration_iter))
        program.append_block(block=loop)
        return program

    @QubitInstrument.CheckConnected
    def start(self):
        """Execute the uploaded instructions."""
        self.device.arm_sequencer()
        self.device.start_sequencer()

    @QubitInstrument.CheckConnected
    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._set_gain()
        self._set_nco()

    @QubitInstrument.CheckConnected
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        self.device.stop_sequencer()

    @QubitInstrument.CheckConnected
    def reset(self):
        """Reset instrument."""
        self.device.reset()

    @QubitInstrument.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        self._set_reference_source()
        self._set_sync_enabled()

    @QubitInstrument.CheckConnected
    def upload(self, sequence: Sequence):
        """Upload sequence to sequencer.

        Args:
            sequence (Sequence): Sequence object containing the waveforms, weights,
            acquisitions and program of the sequence.
        """
        # TODO: Discuss this sequence dump: use DB or files?
        file_path = Path(sys.argv[0]).parent / f"{self.name}_sequence.yml"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            json.dump(obj=sequence.todict(), fp=file)
        getattr(self.device, f"sequencer{self.sequencer}").sequence(file_path)

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path0(self.gain)
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path1(self.gain)

    def _set_nco(self):
        """Enable modulation of pulses and setup NCO frequency."""
        getattr(self.device, f"sequencer{self.sequencer}").mod_en_awg(True)
        getattr(self.device, f"sequencer{self.sequencer}").nco_freq(self.frequency)

    def _set_reference_source(self):
        """Set reference source. Options are 'internal' or 'external'"""
        self.device.reference_source(self.reference_clock)

    def _set_sync_enabled(self):
        """Enable/disable synchronization over multiple instruments."""
        getattr(self.device, f"sequencer{self.sequencer}").sync_en(self.sync_enabled)

    def _initialize_device(self):
        """Initialize device attribute to the corresponding device class."""
        # TODO: We need to update the firmware of the instruments to be able to connect
        self.device = Pulsar(name=self.name, identifier=self.ip)

    def _generate_waveforms(self, pulses: List[Pulse]):
        """Generate I and Q waveforms from a PulseSequence object.

        Args:
            pulse_sequence (PulseSequence): PulseSequence object.

        Returns:
            Dict[str, Dict[str, List]]: Dictionary containing the generated waveforms.
        """
        waveforms_dict: Dict[str, Dict[str, List | int]] = {}

        unique_pulses = []
        idx = 0

        for pulse in pulses:
            if pulse not in unique_pulses:
                unique_pulses.append(pulse)
                pulse.index = idx
                envelope = pulse.envelope()
                waveforms_dict |= {
                    f"{pulse}_I": {"data": (np.real(envelope) + self.offset_i).tolist(), "index": idx},
                    f"{pulse}_Q": {"data": (np.imag(envelope) + self.offset_q).tolist(), "index": idx},
                }
                idx += 2
            else:
                pulse.index = unique_pulses.index(pulse) * 2

        return waveforms_dict

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
    def frequency(self):
        """QbloxPulsar 'frequency' property.

        Returns:
            float: settings.frequency.
        """
        return self.settings.frequency
