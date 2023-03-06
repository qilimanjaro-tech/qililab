"""Time Domain Readout SystemControl class."""
from dataclasses import dataclass, field

from qililab.instruments.awg_analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.instruments import Instruments
from qililab.instruments.signal_generator import SignalGenerator
from qililab.result.result import Result
from qililab.system_controls.system_control_types.time_domain_control_system_control import (
    ControlSystemControl,
)
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter, SystemControlName
from qililab.utils import Factory


@Factory.register
class TimeDomainReadoutSystemControl(ControlSystemControl):
    """TimeDomain Readout SystemControl class."""

    name = SystemControlName.TIME_DOMAIN_READOUT_SYSTEM_CONTROL

    @dataclass
    class TimeDomainReadoutSystemControlSettings(
        ControlSystemControl.ControlSystemControlSettings,
    ):
        """Time Domain Readout System Control settings class."""

        system_control_subcategory = SystemControlSubCategory.TIME_DOMAIN_READOUT
        hardware_demodulation: bool
        adc: AWGAnalogDigitalConverter | None = field(default=None)

        def _supported_instrument_categories(self) -> list[str]:
            """return a list of supported instrument categories."""
            return super()._supported_instrument_categories() + [Category.ADC.value]

    settings: TimeDomainReadoutSystemControlSettings

    def _replace_settings_dicts_with_instrument_objects(self, instruments: Instruments):
        """assign parent awg as the same as adc when it is not defined (it is the same instrument as AWG)"""
        super()._replace_settings_dicts_with_instrument_objects(instruments=instruments)
        if self.adc is None:
            awg_instrument = instruments.get_instrument(alias=self.awg.alias)
            self._check_for_a_valid_instrument(instrument=awg_instrument)
            self.settings.adc = awg_instrument

    @property
    def adc(self):
        """Readout System Control 'adc' property.
        Returns:
            AWG: settings.adc.
        """
        return self.settings.adc

    def __str__(self):
        """String representation of the TimeDomainReadoutSystemControl class."""
        return f"-|{self.signal_generator}|--|{self.adc}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.IF:
            self.settings.intermediate_frequency = float(value)
            # first setup the IF that the DEMODULATION WILL USE
            if self.settings.hardware_demodulation:
                sequencer_id = self.settings.sequencer_id
                self.adc.device.sequencers[sequencer_id].nco_freq(float(value))
            # second setup the IF inside the matrioska (AWG)
            super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            return
        if parameter == Parameter.HARDWARE_DEMODULATION:
            sequencer_id = self.settings.sequencer_id
            self.settings.hardware_demodulation = bool(value)
            self.adc.device.sequencers[sequencer_id].demod_en_acq(bool(value))
            return
        if parameter == Parameter.ACQUISITION_DELAY_TIME:
            return
        if parameter == Parameter.INTEGRATION_LENGTH:
            return
        if parameter == Parameter.INTEGRATION_WEIGHT_I_1:
            return
        if parameter == Parameter.INTEGRATION_WEIGHT_I_2:
            return
        if parameter == Parameter.INTEGRATION_WEIGHT_Q_1:
            return
        if parameter == Parameter.INTEGRATION_WEIGHT_Q_2:
            return
        super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)
        return

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return super()._get_supported_instrument_categories() + [Category.ADC]

    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
        return self.adc.acquire_result()

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        return self.adc.acquisition_delay_time

    def setup(self):
        # In this layer we handle Digitization (ADC) settings
        # 1. Settings
        # all the sequence-related pars (bins, average, etc are handled in parent class awg)

        super().setup()
        # 2. Sequence
        # might have been uploaded above depending on how we organize the brain sequencing
        # 3. Waveforms
        # here it is relevant to set up the waveforms
        # self.awg.setup()
        # self.signal_generator.setup()
