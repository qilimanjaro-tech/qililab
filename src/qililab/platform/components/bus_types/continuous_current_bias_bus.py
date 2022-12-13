""" Continuous Current Bias Bus """

from dataclasses import dataclass

from qililab.platform.components.bus_types.continuous_bus import ContinuousBus
from qililab.system_controls.system_control_types import CurrentBiasSystemControl
from qililab.typings.enums import BusName, BusSubCategory
from qililab.utils import Factory


@Factory.register
class CurrentBiasBus(ContinuousBus):
    """Continuous Current Bias Bus"""

    name = BusName.CONTINUOUS_CURRENT_BIAS_BUS

    @dataclass
    class CurrentBiasBusSettings(ContinuousBus.ContinuousBusSettings):
        """Contains the settings of a specific continuous current bias bus."""

        bus_subcategory = BusSubCategory.CURRENT_BIAS
        system_control: CurrentBiasSystemControl

    settings: CurrentBiasBusSettings
