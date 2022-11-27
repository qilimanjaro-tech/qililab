"""Continuous Readout SystemControl class."""
from dataclasses import dataclass

from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.result.result import Result
from qililab.system_controls.system_control_types.continuous_system_control import (
    ContinuousSystemControl,
)
from qililab.typings import SystemControlSubCategory
from qililab.typings.enums import Category, Parameter, SystemControlName
from qililab.utils import Factory


@Factory.register
class ContinuousReadoutSystemControl(ContinuousSystemControl):
    """Continuous Readout  System Control class."""

    name = SystemControlName.CONTINUOUS_READOUT_SYSTEM_CONTROL

    @dataclass
    class ContinuousReadoutSystemControlSettings(ContinuousSystemControl.ContinuousSystemControlSettings):
        """Continuous Readout System Control settings class."""

        system_control_subcategory = SystemControlSubCategory.CONTINUOUS_READOUT
        vector_network_analyzer = VectorNetworkAnalyzer

    settings: ContinuousReadoutSystemControlSettings

    @property
    def vector_network_analyzer(self):
        """System Control 'vector_network_analyzer' property.
        Returns:
            VectorNetworkAnalyzer: settings.vector_network_analyzer
        """
        return self.settings.vector_network_analyzer

    def _get_supported_instrument_categories(self) -> list[Category]:
        """get supported instrument categories"""
        return [Category.VNA]

    def __str__(self):
        """String representation of the ContinuousReadoutSystemControlSettings class."""
        return f"-|{self.vector_network_analyzer}|-"

    def set_parameter(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """sets a parameter to a specific instrument

        Args:
            parameter (Parameter): parameter settings of the instrument to update
            value (float | str | bool): value to update
            channel_id (int | None, optional): instrument channel to update, if multiple. Defaults to None.
        """
        self.vector_network_analyzer.set_parameter(parameter=parameter, value=value, channel_id=channel_id)

    def acquire_result(self) -> Result:
        """Read the result from the vector networkk analyzer instrument

        Returns:
            Result: Acquired result
        """
        return self.vector_network_analyzer.acquire_result()
