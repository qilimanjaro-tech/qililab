"""HeterodyneSystemControl class."""
from abc import ABC, abstractmethod
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
from qililab.typings.enums import Parameter


@Factory.register
class HeterodyneSystemControl(SystemControl):
    """HeterodyneSystemControl class."""

    name = SystemControlSubcategory.HETERODYNE_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class HeterodyneSystemControlSettings(SystemControl.SystemControlSettings):
        """HeterodyneSystemControlSettings class."""

        awg: AWG
        signal_generator: SignalGenerator
        pulse_length: int = 6000
        IF: float = 0.01
        # LO: float
        gain: float = None
        shots: int = 1000

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

    def heterodyne_mixing(self,I, Q, fLO, dt):
        # This function should probably go to utilities. I also need a better name for it
        N = I.shape[0]

        time = np.linspace(0, N * dt,N)  

        cos = np.cos(2 * np.pi * fLO * time)
        sin = np.sin(2 * np.pi * fLO * time)

        modI = cos*I + sin*Q
        modQ = -sin*I + cos*Q

        return modI, modQ


    def setup(self):
        # TODO: Find a way of managing the tone, LO and IF frequencies

        """ Write the description of this function """
        
        # Clean the memory of the awg
        self.awg.reset()

        # New code : 
        dt = 1 # one nanosecond for GS/s resolution

        I = np.ones(self.settings.pulse_length)  # + scipy.signal.gaussian(waveform_length, std=0.12 * waveform_length)
        Q = np.zeros(self.settings.pulse_length)

        modI, modQ = self.heterodyne_mixing(I, Q, self.settings.IF, dt)

        waveforms = {
            "modI": {
                "data": list(modI),
                "index": 0,
            },
            "modQ": {
                "data": list(modQ),
                "index": 1,
            },
        }

        # ## 1.2. Set LO
        # set LO power in dBm (Marki mixer requires 13dBm + 3dBm from the splitter)
        self.signal_generator.device.power(16)
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

        seq_prog = f"""
        move    {self.settings.shots},R0   #Loop iterator.
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
        if self.settings.gain is not None:
            self.awg.device.sequencer0.gain_awg_path0(self.settings.gain)
            self.awg.device.sequencer0.gain_awg_path1(self.settings.gain)
            print(f"Heterodyne bus set gain to {self.settings.gain}")

        else: 
            print("Gain is not set by Heterodyne bus")

        print(f"Actual gain: {self.awg.device.sequencer0.gain_awg_path0()}")

    def start(self):
        """Start/Turn on the instruments.
        self.signal_generator.device.start()"""

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

        # print(f"Path 0: {self.awg.device.sequencer0.gain_awg_path0()}")
        # print(f"Path 1: {self.awg.device.sequencer0.gain_awg_path1()}")
        
        # self.signal_generator.device.off()
        # Print status of sequencer.
        # print(f"Sequencer State: {self.awg.device.get_sequencer_state(0)}")
        # ## 2.2 Query data and plotting
        # Wait for the acquisition to finish with a timeout period of one minute.
        # print(f"Acquisition state: {self.awg.device.get_acquisition_state(0, 1)}")
        # Move acquisition data from temporary memory to acquisition list.
        self.awg.device.store_scope_acquisition(0, "single")
        # Get acquisition list from instrument.
        single_acq = self.awg.device.get_acquisitions(0)

        # print(single_acq.keys())

        # ## 2.3 should be outside!
        output_I = np.array(single_acq["single"]["acquisition"]["scope"]["path0"]["data"][:6100])
        output_Q = np.array(single_acq["single"]["acquisition"]["scope"]["path1"]["data"][:6100])

        # print(f'output: {output_I}')
        time_vector_demod = np.linspace(0, len(output_I), len(output_I))
        cosalpha = np.cos(2 * np.pi * self.settings.IF * time_vector_demod)
        sinalpha = np.sin(2 * np.pi * self.settings.IF * time_vector_demod)
        demod_matrix = 2 * np.array([[cosalpha, -sinalpha], [sinalpha, cosalpha]])
        result = []
        for it, t, ii, qq in zip(np.arange(output_I.shape[0]), time_vector_demod, output_I, output_Q):
            result.append(demod_matrix[:, :, it] @ np.array([ii, qq]))
        demodulated_signal = np.array(result)

        demodulated_I = demodulated_signal[:, 0]
        demodulated_Q = demodulated_signal[:, 1]
        # ## 2.4 Integrate
        integrated_I = integ.trapz(demodulated_I, dx=1) / len(demodulated_I)  # dx is the spacing between points, in our case 1ns
        integrated_Q = integ.trapz(demodulated_Q, dx=1) / len(demodulated_Q)

        print(f"Actual gain in run: {self.awg.device.sequencer0.gain_awg_path0()}")
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

    
    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """_summary_

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter.value == Parameter.POWER.value:
            self.signal_generator.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            return
        if parameter.value == Parameter.FREQUENCY.value:
            if not isinstance(value, float):
                raise ValueError(f"value must be a float. Current type: {type(value)}")
            self._update_frequency(frequency=value, channel_id=channel_id)
            return
        # the rest of parameters are assigned to the AWG
        if parameter.value == Parameter.GAIN.value:
            self.settings.gain = value
            return
        self.awg.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
