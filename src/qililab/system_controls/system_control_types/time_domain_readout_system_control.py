"""Time Domain Readout SystemControl class."""
from dataclasses import dataclass, field

from qililab.instruments.awg_analog_digital_converter import AWGAnalogDigitalConverter
from qililab.instruments.instruments import Instruments
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
        if parameter in [
            Parameter.BUS_FREQUENCY,
            Parameter.LO_FREQUENCY,
            Parameter.POWER,
            Parameter.GAIN,
            Parameter.GAIN_PATH0,
            Parameter.GAIN_PATH1,
            Parameter.OFFSET_I,
            Parameter.OFFSET_Q,
            Parameter.OFFSET_PATH0,
            Parameter.OFFSET_PATH1,
            Parameter.IF,
            Parameter.HARDWARE_MODULATION,
            Parameter.SYNC_ENABLED,
            Parameter.NUM_BINS,
            Parameter.GAIN_IMBALANCE,
            Parameter.PHASE_IMBALANCE,
        ]:
            super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            return
        # the rest of parameters are assigned to the AWGDigitalAnalogConverter
        self.adc.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

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
