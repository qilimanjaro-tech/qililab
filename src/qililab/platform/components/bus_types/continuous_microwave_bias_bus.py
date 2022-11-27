""" Continuous MicroWave Bias Bus """

from dataclasses import dataclass

from qililab.platform.components.bus_types.continuous_bus import ContinuousBus
from qililab.system_controls.system_control_types import MicroWaveBiasSystemControl
from qililab.typings.enums import BusName, BusSubCategory
from qililab.utils import Factory


@Factory.register
class MicroWaveBiasBus(ContinuousBus):
    """Continuous MicroWave Bias Bus"""

    name = BusName.CONTINUOUS_MICROWAVE_BIAS_BUS

    @dataclass
    class MicroWaveBiasBusSettings(ContinuousBus.ContinuousBusSettings):
        """Contains the settings of a specific continuous current bias bus."""

        bus_subcategory = BusSubCategory.MICROWAVE_BIAS
        system_control: MicroWaveBiasSystemControl

    settings: MicroWaveBiasBusSettings
