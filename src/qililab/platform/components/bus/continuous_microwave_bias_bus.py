""" Continuous MicroWave Bias Bus """

from dataclasses import dataclass

from qililab.instruments import MicroWaveBiasSystemControl
from qililab.platform.components.bus import ContinuousBus
from qililab.typings.enums import BusSubCategory


class MicroWaveBiasBus(ContinuousBus):
    """Continuous MicroWave Bias Bus"""

    @dataclass
    class MicroWaveBiasBusSettings(ContinuousBus.ContinuousBusSettings):
        """Contains the settings of a specific continuous current bias bus."""

        bus_subcategory = BusSubCategory.MICROWAVE_BIAS
        system_control: MicroWaveBiasSystemControl

    settings: MicroWaveBiasBusSettings
