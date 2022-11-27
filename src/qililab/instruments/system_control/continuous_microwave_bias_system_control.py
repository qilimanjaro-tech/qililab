"""Continuous MicroWave Bias SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.signal_generator import SignalGenerator
from qililab.instruments.system_control.continuous_system_control import (
    ContinuousSystemControl,
)
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter
from qililab.utils import Factory


@Factory.register
class MicroWaveBiasSystemControl(ContinuousSystemControl):
    """Continuous MicroWave Bias System Control class."""

    @dataclass
    class MicroWaveBiasSystemControlSettings(ContinuousSystemControl.ContinuousSystemControlSettings):
        """Continuous MicroWave BiasSystem Control settings class."""

        system_control_subcategory = SystemControlSubCategory.MICROWAVE_BIAS
        signal_generator: SignalGenerator

    settings: MicroWaveBiasSystemControlSettings

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.
        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    def __str__(self):
        """String representation of the MicroWaveBiasSystemControl class."""
        return f"-|{self.signal_generator}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        self.signal_generator.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return [Category.SIGNAL_GENERATOR]
