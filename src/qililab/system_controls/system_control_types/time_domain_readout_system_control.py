"""Time Domain Readout SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.digital_analog_converter import AWGDigitalAnalogConverter
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
        awg_dac: AWGDigitalAnalogConverter

        def __post_init__(self):
            """assign parent awg as the same as awg_dac"""
            super().__post_init__()
            self.awg_dac = self.awg

        def _supported_instrument_categories(self) -> list[str]:
            """return a list of supported instrument categories."""
            return super()._supported_instrument_categories() + [Category.AWG_DAC.value]

    settings: TimeDomainReadoutSystemControlSettings

    @property
    def awg_dac(self):
        """Readout System Control 'awg_dac' property.
        Returns:
            AWG: settings.awg_dac.
        """
        return self.settings.awg_dac

    def __str__(self):
        """String representation of the TimeDomainReadoutSystemControl class."""
        return f"-|{self.signal_generator}|--|{self.awg_dac}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter in [
            Parameter.LO_FREQUENCY,
            Parameter.POWER,
            Parameter.GAIN,
            Parameter.OFFSET_I,
            Parameter.OFFSET_Q,
            Parameter.IF,
            Parameter.HARDWARE_MODULATION,
            Parameter.SYNC_ENABLED,
            Parameter.NUM_BINS,
            Parameter.GAIN_IMBALANCE,
            Parameter.PHASE_IMBALANCE,
        ]:
            super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)
        # the rest of parameters are assigned to the AWGDigitalAnalogConverter
        self.awg_dac.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return super()._get_supported_instrument_categories() + [Category.AWG_DAC]

    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
        return self.awg_dac.acquire_result()
