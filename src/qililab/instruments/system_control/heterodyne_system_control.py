"""HeterodyneSystemControl class."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Tuple

import numpy as np
import scipy.integrate as integ

from qililab.constants import RUNCARD
from qililab.instruments.awg import AWG
from qililab.instruments.instruments import Instruments
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.result.heterodyne_result import HeterodyneResult
from qililab.typings import Category, SystemControlSubcategory
from qililab.utils import Factory


@Factory.register
class HeterodyneSystemControl(SystemControl):
    """HeterodyneSystemControl class."""

    name = SystemControlSubcategory.HETERODYNE_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class HeterodyneSystemControlSettings(SystemControl.SystemControlSettings):
        """HeterodyneSystemControlSettings class."""

        awg: AWG
        signal_generator: SignalGenerator

        def __iter__(
            self,
        ) -> Generator[Tuple[str, SignalGenerator | AWG | int], None, None]:
            """Iterate over Bus elements.

            Yields:
                Tuple[str, ]: _description_
            """
            for name, value in self.__dict__.items():
                if name in [Category.AWG.value, Category.SIGNAL_GENERATOR.value]:
                    yield name, value

    settings: HeterodyneSystemControlSettings

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

    def setup(self, frequencies: List[float]):
        """Setup instruments.
        min_freq = np.min(frequencies)
        self.signal_generator.device.frequency = min_freq + self.awg.frequency
        self.awg.multiplexing_frequencies = list(self.signal_generator.device.frequency - np.array(frequencies))
        self.awg.setup()
        self.signal_generator.device.setup()"""
        # print('[Heterodyne SysCtrl] Entered setup')
        self.awg.device.reset()
        # # 1. Setup/Preparation
        # ## 1.1 Generate Waveforms
        # Waveform parameters
        waveform_length = 6000  # nanoseconds
        times_vector = np.arange(0, waveform_length + 0.5, 1)  # 1ns per sample
        self.freq_if = 0.01  # in GHz to match nanosecond units
        envelope_I = np.ones(waveform_length)  # + scipy.signal.gaussian(waveform_length, std=0.12 * waveform_length)
        envelope_Q = np.zeros(waveform_length)

        cosalpha = np.cos(2 * np.pi * self.freq_if * times_vector)
        sinalpha = np.sin(2 * np.pi * self.freq_if * times_vector)
        mod_matrix = np.array([[cosalpha, sinalpha], [-sinalpha, cosalpha]])
        result = []
        for it, t, ii, qq in zip(np.arange(envelope_I.shape[0]), times_vector, envelope_I, envelope_Q):
            result.append(mod_matrix[:, :, it] @ np.array([ii, qq]))
        modulated_signal = np.array(result)
        modulated_I, modulated_Q = modulated_signal.transpose()
        # Waveform dictionary (data will hold the samples and index will be used to select the waveforms in the instrument).
        waveforms = {
            "modI": {
                "data": list(modulated_I),
                "index": 0,
            },
            "modQ": {
                "data": list(modulated_Q),
                "index": 1,
            },
        }

        # ## 1.2. Set LO
        self.signal_generator.device.power(
            16
        )  # set LO power in dBm (Marki mixer requires 13dBm + 3dBm from the splitter)
        # self.signal_generator.device.frequency(7e9)
        self.signal_generator.device.on()
        # ## 1.2 Acquisition
        # Acquisitions
        acquisitions = {
            "single": {"num_bins": 1, "index": 0},
            "multiple_0": {"num_bins": 1, "index": 1},
            "multiple_1": {"num_bins": 1, "index": 2},
            "multiple_2": {"num_bins": 1, "index": 3},
            "avg": {"num_bins": 1, "index": 4},
        }

        # ## 1.3 Sequence
        # Sequence program.
        # seq_prog = """
        # play    0,1,4     #Play waveforms and wait 4ns.
        # acquire 0,0,20000 #Acquire waveforms and wait remaining duration of scope acquisition.
        # wait    100
        # stop              #Stop.orms and wait remaining duration of scope acquisition.
        # stop              #Stop.
        # """
        seq_prog = """
        move    1000,R0   #Loop iterator.
        loop:
        play    0,1,4     #Play waveforms and wait 4ns.
        acquire 0,0,20000 #Acquire waveforms and wait remaining duration of scope acquisition.
        wait    100
        loop    R0,@loop  #Run until number of iterations is done.
        stop              #Stop.orms and wait remaining duration of scope acquisition.
        stop              #Stop.
        """
        # ## 1.4 Upload all
        # Add sequence to single dictionary and write to JSON file.
        sequence = {
            "waveforms": waveforms,
            "weights": {},
            "acquisitions": acquisitions,
            "program": seq_prog,
        }
        with open("sequence.json", "w", encoding="utf-8") as file:
            json.dump(sequence, file, indent=4)
            file.close()
        self.awg.device.sequencer0.sequence("sequence.json")

        # ## 1.5 Configurations
        # Configure the sequencer to trigger the scope acquisition.
        self.awg.device.scope_acq_sequencer_select(0)
        self.awg.device.scope_acq_trigger_mode_path0("sequencer")
        self.awg.device.scope_acq_trigger_mode_path1("sequencer")
        # Map sequencer to specific outputs (but first disable all sequencer connections)
        for sequencer in self.awg.device.sequencers:
            for out in range(0, 2):
                sequencer.set("channel_map_path{}_out{}_en".format(out % 2, out), False)
        self.awg.device.sequencer0.channel_map_path0_out0_en(True)
        self.awg.device.sequencer0.channel_map_path1_out1_en(True)
        self.awg.device.sequencer0.mod_en_awg(False)
        # enable hardware average
        self.awg.device.scope_acq_avg_mode_en_path0(True)
        self.awg.device.scope_acq_avg_mode_en_path1(True)
        # set gain
        self.awg.device.sequencer0.gain_awg_path0(1.0)
        self.awg.device.sequencer0.gain_awg_path1(1.0)

    def start(self):
        """Start/Turn on the instruments.
        self.signal_generator.device.start()"""
        # print('[Heterodyne SysCtrl] Entered start')

    def run(self, pulse_sequence: PulseSequence, nshots: int, repetition_duration: int, path: Path):
        """Change the SignalGenerator frequency if needed and run the given pulse sequence.
        if pulse_sequence.frequency is not None and pulse_sequence.frequency != self.frequency:
            self.signal_generator.device.frequency = pulse_sequence.frequency + self.awg.frequency
            self.signal_generator.device.setup()
        return self.awg.run(
            pulse_sequence=pulse_sequence,
            nshots=nshots,
            repetition_duration=repetition_duration,
            path=path,
        )"""
        # print('[Heterodyne SysCtrl] Entered run')
        # # 2. Running the Bus
        # ## 2.1 Arm & Run
        # Arm and start sequencer.
        self.awg.device.arm_sequencer(0)
        self.awg.device.start_sequencer()
        # self.signal_generator.device.off()
        # Print status of sequencer.
        # print("Status:")
        # print(self.awg.device.get_sequencer_state(0))
        # ## 2.2 Query data and plotting
        # Wait for the acquisition to finish with a timeout period of one minute.
        self.awg.device.get_acquisition_state(0, 1)
        # Move acquisition data from temporary memory to acquisition list.
        self.awg.device.store_scope_acquisition(0, "single")
        # Get acquisition list from instrument.
        single_acq = self.awg.device.get_acquisitions(0)

        # ## 2.3 should be outside!
        output_I = np.array(single_acq["single"]["acquisition"]["scope"]["path0"]["data"][:6100])
        output_Q = np.array(single_acq["single"]["acquisition"]["scope"]["path1"]["data"][:6100])
        time_vector_demod = np.linspace(0, len(output_I), len(output_I))
        cosalpha = np.cos(2 * np.pi * self.freq_if * time_vector_demod)
        sinalpha = np.sin(2 * np.pi * self.freq_if * time_vector_demod)
        demod_matrix = 2 * np.array([[cosalpha, -sinalpha], [sinalpha, cosalpha]])
        result = []
        for it, t, ii, qq in zip(np.arange(output_I.shape[0]), time_vector_demod, output_I, output_Q):
            result.append(demod_matrix[:, :, it] @ np.array([ii, qq]))
        demodulated_signal = np.array(result)
        demodulated_I = demodulated_signal[:, 0]
        demodulated_Q = demodulated_signal[:, 1]
        # ## 2.4 Integrate
        integrated_I = integ.trapz(demodulated_I, dx=1) / len(
            demodulated_I
        )  # dx is the spacing between points, in our case 1ns
        integrated_Q = integ.trapz(demodulated_Q, dx=1) / len(demodulated_Q)
        # print(integrated_I,integrated_Q)
        return HeterodyneResult(integrated_i=integrated_I, integrated_q=integrated_Q)

    @property
    def awg_frequency(self):
        """SystemControl 'awg_frequency' property."""
        return self.awg.frequency

    @property
    def frequency(self):
        """SystemControl 'frequency' property."""
        return (
            self.signal_generator.frequency - self.awg.frequency
            if self.signal_generator.frequency is not None
            else None
        )

    @frequency.setter
    def frequency(self, target_freqs: List[float]):
        """SystemControl 'frequency' property setter."""
        self.signal_generator.frequency = target_freqs[0] + self.awg.frequency
        self.signal_generator.setup()

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.
        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    @property
    def awg(self):
        """Bus 'awg' property.
        Returns:
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.awg

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        if isinstance(self.awg, QubitReadout):
            return self.awg.acquisition_delay_time
        raise ValueError("AWG is not a QubitReadout instance.")

    def __iter__(self):
        """Redirect __iter__ magic method."""
        return self.settings.__iter__()

    def to_dict(self):
        """Return a dict representation of the HeterodyneSystemControl class."""
        return {
            RUNCARD.ID: self.id_,
            RUNCARD.CATEGORY: self.settings.category.value,
            RUNCARD.SUBCATEGORY: self.settings.subcategory.value,
        } | {key: value.alias for key, value in self}

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """Replace dictionaries from settings into its respective instrument classes."""
        for name, value in self.settings:
            if isinstance(value, str):
                instrument_object = instruments.get_instrument(alias=value)
                setattr(self.settings, name, instrument_object)

    def __str__(self):
        """String representation of the HeterodyneSystemControl class."""
        return f"{self.awg}|----|{self.signal_generator}"
