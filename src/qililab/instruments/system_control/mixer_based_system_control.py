"""MixerBasedSystemControl class."""
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Tuple

import json
import numpy as np

from qililab.constants import RUNCARD
from qililab.instruments.awg import AWG
from qililab.instruments.instruments import Instruments
from qililab.instruments.qubit_readout import QubitReadout
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseBusSchedule
from qililab.typings import Category, SystemControlSubcategory
from qililab.typings.enums import Parameter
from qililab.utils import Factory
from scipy.signal.windows import gaussian

@Factory.register
class MixerBasedSystemControl(SystemControl):
    """MixerBasedSystemControl class."""

    name = SystemControlSubcategory.MIXER_BASED_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class MixerBasedSystemControlSettings(SystemControl.SystemControlSettings):
        """MixerBasedSystemControlSettings class."""

        awg: AWG
        signal_generator: SignalGenerator
        pulse_length: int = 100
        sequence_manual: bool = True
        gain: float = None
        IF: float = 0.01
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

    settings: MixerBasedSystemControlSettings

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)
    
    def heterodyne_mixing(self, I, Q, fLO, dt):
        # This function should probably go to utilities. I also need a better name for it
        N = I.shape[0]

        time = np.linspace(0, N * dt, N)

        cos = np.cos(2 * np.pi * fLO * time)
        sin = np.sin(2 * np.pi * fLO * time)

        modI = cos * I + sin * Q
        modQ = -sin * I + cos * Q

        return modI, modQ


    def setup(self):
        """Setup instruments."""
       
       # New code :
        dt = 1  # one nanosecond for GS/s resolution

        I = np.array(gaussian(self.settings.pulse_length,10)) # + scipy.signal.gaussian(waveform_length, std=0.12 * waveform_length)
        Q = np.zeros(self.settings.pulse_length)

        self.modI, self.modQ = self.heterodyne_mixing(I, Q, self.settings.IF, dt)
        self.waveforms = {
            "modI": {
                "data": list(self.modI),
                "index": 0,
            },
            "modQ": {
                "data": list(self.modQ),
                "index": 1,
            },
        }
        
        # Generates a hardcoded sequence here in the Heterodyne
        if self.settings.sequence_manual:
            self._prepare_sequence_manually(self.modI, self.modQ, self.waveforms)

       

        # Map sequencer to specific outputs (but first disable all sequencer connections)
        for sequencer in self.awg.device.sequencers:
            for out in range(0, 2):
                sequencer.set("channel_map_path{}_out{}_en".format(out % 2, out), False)
        self.awg.device.sequencer0.channel_map_path0_out0_en(True)
        self.awg.device.sequencer0.channel_map_path1_out1_en(True)
        self.awg.device.sequencer0.mod_en_awg(False)

        # set gain
        if self.settings.gain is not None:
            self.awg.device.sequencer0.gain_awg_path0(self.settings.gain)
            self.awg.device.sequencer0.gain_awg_path1(self.settings.gain)
            print(f'gain set to {self.settings.gain}')
            
            
    def _prepare_sequence_manually(self, modI, modQ, waveforms):

        # ## 1.2. Set LO
        # set LO power in dBm (Marki mixer requires 13dBm + 3dBm from the splitter)
        # self.signal_generator.device.power(16) # This does not need to be hardcoded here. The runcard initiates it correctly
        self.signal_generator.device.on()


        seq_prog = f"""
        move    {self.settings.shots},R0   #Loop iterator.
        loop:
        wait_sync   4
        play    0,1,7000     #Play waveforms and wait 7000ns.
        wait_sync   4
        wait    8000
        loop    R0,@loop  #Run until number of iterations is done.
        stop              #Stop.
        """
        
        # ## 1.4 Upload all
        # Add sequence to single dictionary and write to JSON file.
        sequence = {
            "waveforms": waveforms,
            "weights": {},
            "acquisitions": {},
            "program": seq_prog,
        }
        with open("sequence.json", "w", encoding="utf-8") as file:
            json.dump(sequence, file, indent=4)
            file.close()
        self.awg.device.sequencer0.sequence("sequence.json")
        # print(f"Heterodyne bus set gain to {self.settings.gain}")

        # else:
        # print("Gain is not set by Heterodyne bus")

        # print(f"Actual gain: {self.awg.device.sequencer0.gain_awg_path0()}")

    def start(self):
        """Start/Turn on the instruments."""
        self.signal_generator.start()

    def run(self, pulse_bus_schedule: PulseBusSchedule, nshots: int, repetition_duration: int, path: Path):
        """Change the SignalGenerator frequency if needed and run the given pulse sequence."""
       
        # set gain
        if self.settings.gain is not None:
            self.awg.device.sequencer0.gain_awg_path0(self.settings.gain)
            self.awg.device.sequencer0.gain_awg_path1(self.settings.gain)
            print(f'gain set to {self.settings.gain}')
            
        print(f"Actual gain: {self.awg.device.sequencer0.gain_awg_path0()}")
        self.awg.device.arm_sequencer(0)

        self.awg.device.start_sequencer(0)

    def _update_frequency(self, frequency: float, channel_id: int | None = None):
        """update frequency to the signal generator and AWG

        Args:
            frequency (float): the bus final frequency (AWG + Signal Generator)
            channel_id (int | None, optional): AWG Channel. Defaults to None.
        """
        if channel_id is None:
            raise ValueError("channel not specified to update instrument")
        if channel_id > self.awg.num_sequencers - 1:
            raise ValueError(
                f"the specified channel_id:{channel_id} is out of range. "
                + f"Number of sequencers is {self.awg.num_sequencers}"
            )
        signal_generator_frequency = frequency - self.awg.frequencies[channel_id]
        self.signal_generator.set_parameter(parameter=Parameter.FREQUENCY, value=signal_generator_frequency)

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """set parameter for an instrument

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
        self.awg.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

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
        """Return a dict representation of the MixerBasedSystemControl class."""
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
        """String representation of the MixerBasedSystemControl class."""
        return f"{self.awg}|----|{self.signal_generator}"
