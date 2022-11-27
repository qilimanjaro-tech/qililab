"""Time Domain Readout SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.qubit_readout import AWGReadout
from qililab.instruments.system_control.time_domain_baseband_system_control import (
    BaseBandSystemControl,
)
from qililab.instruments.system_control.time_domain_control_system_control import (
    ControlSystemControl,
)
from qililab.result.result import Result
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter
from qililab.utils import Factory


@Factory.register
class TimeDomainReadoutSystemControl(BaseBandSystemControl, ControlSystemControl):
    """TimeDomain Readout SystemControl class."""

    @dataclass
    class TimeDomainReadoutSystemControlSettings(
        BaseBandSystemControl.BaseBandSystemControlSettings,
        ControlSystemControl.ControlSystemControlSettings,
    ):
        """Time Domain Readout System Control settings class."""

        system_control_subcategory = SystemControlSubCategory.TIME_DOMAIN_READOUT
        awg: AWGReadout

    settings: TimeDomainReadoutSystemControlSettings

    def __str__(self):
        """String representation of the TimeDomainReadoutSystemControl class."""
        return f"-|{self.signal_generator}|--|{self.current_source}|--|{self.awg}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        if parameter in [Parameter.FREQUENCY, Parameter.POWER]:
            super(ControlSystemControl, self).set_parameter(parameter=parameter, value=value, channel_id=channel_id)
        # the rest of parameters are assigned to the BaseBandSystemControl
        super(BaseBandSystemControl, self).set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return [
            *set(
                super(BaseBandSystemControl, self)._get_supported_instrument_categories()
                + super(ControlSystemControl, self)._get_supported_instrument_categories()
            )
        ]

    def acquire_result(self) -> Result:
        """Read the result from the AWG instrument

        Returns:
            Result: Acquired result
        """
        return self.awg.acquire_result()
