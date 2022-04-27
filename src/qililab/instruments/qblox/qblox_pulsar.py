"""Qblox pulsar class"""
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Dict, List

import numpy as np
from qblox_pysequence.block import Loop
from qblox_pysequence.instructions import acquire, play, wait
from qblox_pysequence.program import Program
from qblox_pysequence.sequence import Sequence

from qililab.instruments.instrument import Instrument
from qililab.instruments.pulse.pulse import Pulse
from qililab.instruments.pulse.pulse_sequence import PulseSequence
from qililab.instruments.qblox.qblox_pulsar_qrm import QbloxPulsarQRM
from qililab.instruments.qubit_readout import QubitReadout
from qililab.typings import Pulsar, ReferenceClock


class QbloxPulsar(Instrument):
    """Qblox pulsar class.

    Args:
        device (Pulsar): Instance of the Qblox Pulsar class used to connect to the instrument.
        settings (QbloxPulsarSettings): Settings of the instrument.
    """

    @dataclass
    class QbloxPulsarSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific pulsar.

        Args:
            reference_clock (str): Clock to use for reference. Options are 'internal' or 'external'.
            sequencer (int): Index of the sequencer to use.
            sync_enabled (bool): Enable synchronization over multiple instruments.
            gain (float): Gain step used by the sequencer.
            hardware_average (int): Hardware average. Number of shots used when executing a sequence.
            software_average (float): Software average.
            repetition_duration (int): Duration (ns) of the whole program.
            delay_between_pulses (int): Delay (ns) between two consecutive pulses.
            delay_before_readout (int): Delay (ns) between the readout pulse and the acquisition.
        """

        reference_clock: ReferenceClock
        sequencer: int
        sync_enabled: bool
        gain: float
        hardware_average: ClassVar[int]
        software_average: ClassVar[int]
        repetition_duration: ClassVar[int]
        delay_between_pulses: ClassVar[int]
        delay_before_readout: ClassVar[int]

        def __post_init__(self):
            """Cast reference_clock to its corresponding Enum class"""
            super().__post_init__()
            self.reference_clock = ReferenceClock(self.reference_clock)

    device: Pulsar
    settings: QbloxPulsarSettings

    def connect(self):
        """Establish connection with the instrument. Initialize self.device variable."""
        super().connect()
        self.initial_setup()

    def execute(self, pulse_sequence: PulseSequence):
        """Run execution of a pulse sequence.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.

        Returns:
            (Dict | None): Returns a dict with the acquisitions for the QRM and None for the QCM.
        """
        sequence = self._translate_pulse_sequence(pulse_sequence=pulse_sequence)
        self.upload(sequence=sequence)
        self.start()
        if isinstance(self, QbloxPulsarQRM):
            return self.get_acquisitions()

    def _translate_pulse_sequence(self, pulse_sequence: PulseSequence):
        """Translate a pulse sequence into a Q1ASM program and a waveform dictionary.

        Args:
            pulse_sequence (PulseSequence): Pulse sequence to translate.

        Returns:
            Sequence: Qblox Sequence object containing the program and waveforms.
        """
        waveforms_dict = self._generate_waveforms(pulse_sequence=pulse_sequence)
        program = self._generate_program(pulse_sequence=pulse_sequence)
        # FIXME: (Joel) Add waveforms and program in Sequence constructor.
        sequence = Sequence()
        sequence.set_waveforms(waveforms=waveforms_dict)
        sequence.set_program(program=program)
        return sequence

    def _generate_program(self, pulse_sequence: PulseSequence):
        """Generate Q1ASM program

        Args:
            pulse_sequence (PulseSequence): Pulse sequence.

        Returns:
            Program: Q1ASM program.
        """
        pulses = pulse_sequence.pulses
        program = Program()
        loop = Loop(name="loop", iterations=self.hardware_average)
        loop.append_component(wait(time=pulses[0].start))

        for i, pulse in enumerate(pulses):
            if i < len(pulses) - 1:
                pulse_wait = pulses[i + 1].start - pulse.start
            loop.append_component(play(waveform_0=pulse.index, waveform_1=pulse.index + 1, wait=pulse_wait))

        if isinstance(self, QubitReadout):
            loop.append_component(acquire(acq_index=0, bin_index=1, wait=4))

        loop.append_component(wait(time=self.repetition_duration - loop.duration_iter))
        program.append_loop(loop=loop)
        return program

    @Instrument.CheckConnected
    def start(self):
        """Execute the uploaded instructions."""
        self.device.arm_sequencer()
        self.device.start_sequencer()

    @Instrument.CheckConnected
    def setup(self):
        """Set Qblox instrument calibration settings."""
        self._set_gain()

    @Instrument.CheckConnected
    def stop(self):
        """Stop the QBlox sequencer from sending pulses."""
        self.device.stop_sequencer()

    @Instrument.CheckConnected
    def reset(self):
        """Reset instrument."""
        self.device.reset()

    @Instrument.CheckConnected
    def initial_setup(self):
        """Initial setup of the instrument."""
        self._set_reference_source()
        self._set_sync_enabled()

    @Instrument.CheckConnected
    def upload(self, sequence: Sequence):
        """Upload sequence to sequencer.

        Args:
            sequence_path (str): Path to the json file containing the waveforms,
            weights, acquisitions and program of the sequence.
        """
        # TODO: Discuss this sequence dump: use DB or files?
        file_path = Path(sys.argv[0]).parent / f"{self.name}_sequence.json"
        with open(file=file_path, mode="w", encoding="utf-8") as file:
            json.dump(obj=sequence, fp=file, indent=4)
        getattr(self.device, f"sequencer{self.sequencer}").sequence(file_path)

    def _set_gain(self):
        """Set gain of sequencer for all paths."""
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path0(self.gain)
        getattr(self.device, f"sequencer{self.sequencer}").gain_awg_path1(self.gain)

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

    def _generate_waveforms(self, pulse_sequence: PulseSequence):
        """Generate I and Q waveforms from a PulseSequence object.

        Args:
            pulse_sequence (PulseSequence): PulseSequence object.

        Returns:
            Dict[str, Dict[str, List]]: Dictionary containing the generated waveforms.
        """
        waveforms_dict: Dict[str, Dict[str, List | int]] = {}

        unique_pulses = []
        idx = 0

        for pulse in pulse_sequence.pulses:
            if pulse not in unique_pulses:
                unique_pulses.append(pulse)
                pulse.index = idx
                mod_waveforms = self._quadrature_amplitude_modulation(pulse=pulse)
                for mod in ["I", "Q"]:
                    waveforms_dict |= {
                        f"{pulse.serial()}_mod{mod}": {"data": mod_waveforms[:, 0] + pulse.offset_i, "index": idx}
                    }
                    idx += 1
            else:
                pulse.index = unique_pulses.index(pulse) * 2

        return waveforms_dict

    def _quadrature_amplitude_modulation(self, pulse: Pulse) -> np.ndarray:
        """Applies digital quadrature amplitude modulation (QAM) to the pulse envelope.

        Args:
            pulse (Pulse): Pulse object.

        Returns:
            ndarray: Modulated waveform
        """
        envelope = pulse.envelope
        envelopes = [np.real(envelope), np.imag(envelope)]
        time = np.arange(pulse.duration) * 1e-9
        cosalpha = np.cos(2 * np.pi * pulse.frequency * time + pulse.phase)
        sinalpha = np.sin(2 * np.pi * pulse.frequency * time + pulse.phase)
        mod_matrix = np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
        return np.einsum("abt,bt->ta", mod_matrix, envelopes)

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
    def hardware_average(self):
        """QbloxPulsar 'hardware_average' property.

        Returns:
            int: settings.hardware_average.
        """
        return self.settings.hardware_average

    @property
    def software_average(self):
        """QbloxPulsar 'software_average' property.

        Returns:
            int: settings.software_average.
        """
        return self.settings.software_average

    @property
    def delay_between_pulses(self):
        """QbloxPulsar 'delay_between_pulses' property.

        Returns:
            int: settings.delay_between_pulses.
        """
        return self.settings.delay_between_pulses

    @property
    def delay_before_readout(self):
        """QbloxPulsar 'delay_before_readout' property.

        Returns:
            int: settings.delay_before_readout.
        """
        return self.settings.delay_before_readout

    @property
    def repetition_duration(self):
        """QbloxPulsar 'repetition_duration' property.

        Returns:
            int: settings.repetition_duration.
        """
        return self.settings.repetition_duration
