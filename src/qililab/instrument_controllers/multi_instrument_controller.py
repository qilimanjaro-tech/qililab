"""Multi Instrument Controller class"""
from dataclasses import dataclass

from qililab.instrument_controllers.instrument_controller import (
    InstrumentController,
    InstrumentControllerSettings,
)
from qililab.typings.enums import InstrumentControllerSubCategory


class MultiInstrumentController(InstrumentController):
    """Controller device that controls multiple instruments.

    Args:
        settings (MultiInstrumentControllerSettings): Settings of the Multi Instrument Controller.
    """

    @dataclass
    class MultiInstrumentControllerSettings(InstrumentControllerSettings):
        """Contains the settings of a specific Multi Instrument Controller.

        Args:
            subcategory (InstrumentControllerSubCategory): Subcategory type of the Instrument Controller.
                                                            In this case 'MULTI'.
        """

        subcategory = InstrumentControllerSubCategory.MULTI

    settings: MultiInstrumentControllerSettings
