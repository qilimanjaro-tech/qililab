"""VNASystemControl class."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, List, Tuple

import numpy as np
import scipy.integrate as integ

from qililab.constants import RUNCARD
from qililab.instruments.awg import AWG
from qililab.instruments.instruments import Instruments
from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.instruments.keysight.e5080b_vna import E5080B
from qililab.instruments.system_control.system_control import SystemControl
from qililab.pulse import PulseSequence
from qililab.result.heterodyne_result import HeterodyneResult
from qililab.typings import Category, SystemControlSubcategory, Parameter
from qililab.utils import Factory


@Factory.register
class VNASystemControl(SystemControl):
    """VNASystemControl class."""

    name = SystemControlSubcategory.VNA_SYSTEM_CONTROL

    @dataclass(kw_only=True)
    class VNASystemControlSettings(SystemControl.SystemControlSettings):
        """VNASystemControlSettings class."""

        vna: VectorNetworkAnalyzer
        

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

    settings: VNASystemControlSettings

    @property
    def vna(self):
        """Bus 'vna' property.
        Returns:
            .
        """
        return self.settings.vna

    # def set_parameter(self, parameter: Parameter, value: float, **kw):
        
    #     if parameter == Parameter.GAIN:
    #         self.settings.gain = value
    #         print('Doing something to change gain')
    #         self.awg.device.reset()
    #         print('reset awg OK')
    #         self.awg.device.sequencer0.gain_awg_path0(value)
    #         self.awg.device.sequencer0.gain_awg_path1(value)
    #         print(f'[CW Sys Ctrl] Called Set Parameter {kw}')

    def __init__(self, settings: dict, instruments: Instruments):
        super().__init__(settings=settings)
        self._replace_settings_dicts_with_instrument_objects(instruments=instruments)

    def setup(self, frequencies: List[float]):
        """Setup instruments."""

        print('Entered setup Syst Ctrl')
        self.settings.vna.setup()

        print('Finished setup')




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
        integrated_I = integ.trapz(demodulated_I, dx=1) / len(demodulated_I)  # dx is the spacing between points, in our case 1ns
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
        """Return a dict representation of the VNASystemControl class."""
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
        """String representation of the VNASystemControl class."""
        return f"{self.awg}|----|{self.signal_generator}"
