""" Continuous Current Bias Bus """

from dataclasses import dataclass

from qililab.instruments import CurrentBiasSystemControl
from qililab.platform.components.bus import ContinuousBus
from qililab.typings.enums import BusSubCategory


class CurrentBiasBus(ContinuousBus):
    """Continuous Current Bias Bus"""

    @dataclass
    class CurrentBiasBusSettings(ContinuousBus.ContinuousBusSettings):
        """Contains the settings of a specific continuous current bias bus."""

        bus_subcategory = BusSubCategory.CURRENT_BIAS
        system_control: CurrentBiasSystemControl

    settings: CurrentBiasBusSettings
