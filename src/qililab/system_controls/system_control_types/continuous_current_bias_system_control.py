"""Continuous Current Bias SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.current_source import CurrentSource
from qililab.system_controls.system_control_types.continuous_system_control import (
    ContinuousSystemControl,
)
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter, SystemControlName
from qililab.utils import Factory


@Factory.register
class CurrentBiasSystemControl(ContinuousSystemControl):
    """Continuous Current Bias System Control class."""

    name = SystemControlName.CONTINUOUS_CURRENT_BIAS_SYSTEM_CONTROL

    @dataclass
    class CurrentBiasSystemControlSettings(ContinuousSystemControl.ContinuousSystemControlSettings):
        """Continuous Current BiasSystem Control settings class."""

        system_control_subcategory = SystemControlSubCategory.CURRENT_BIAS
        current_source: CurrentSource

        def _supported_instrument_categories(self) -> list[str]:
            """return a list of supported instrument categories."""
            return [Category.CURRENT_SOURCE.value]

    settings: CurrentBiasSystemControlSettings

    @property
    def current_source(self):
        """Bus 'current_source' property.
        Returns:
            SignalGenerator: settings.current_source.
        """
        return self.settings.current_source

    def __str__(self):
        """String representation of the CurrentBiasSystemControl class."""
        return f"-|{self.current_source}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        self.current_source.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return [Category.CURRENT_SOURCE]
