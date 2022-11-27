"""Time Domain BaseBand SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.current_source import CurrentSource
from qililab.instruments.system_control.time_domain_system_control import (
    TimeDomainSystemControl,
)
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter
from qililab.utils import Factory


@Factory.register
class BaseBandSystemControl(TimeDomainSystemControl):
    """BaseBand SystemControl class."""

    @dataclass
    class BaseBandSystemControlSettings(TimeDomainSystemControl.TimeDomainSystemControlSettings):
        """Time Domain BaseBand System Control settings class."""

        system_control_subcategory = SystemControlSubCategory.BASEBAND
        current_source: CurrentSource

    settings: BaseBandSystemControlSettings

    @property
    def current_source(self):
        """System Control 'current_source' property.
        Returns:
            SignalGenerator: settings.current_source.
        """
        return self.settings.current_source

    def __str__(self):
        """String representation of the BaseBandSystemControl class."""
        return f"{super().__str__()}-|{self.current_source}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter == Parameter.CURRENT:
            self.current_source.set_parameter(parameter=parameter, value=value, channel_id=channel_id)
            return

        # the rest of parameters are assigned to the TimeDomainSystemControl
        super().set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return super()._get_supported_instrument_categories() + [Category.CURRENT_SOURCE]
