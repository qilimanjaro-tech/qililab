"""Single Instrument Controller class"""
from qililab.instrument_controllers.instrument_controller import InstrumentController


class SingleInstrumentController(InstrumentController):
    """Controller device that only controls one single instrument.

    Args:
        settings (SingleInstrumentControllerSettings): Settings of the single instrument controller.
        number_available_modules (int): Number of modules available in the Instrument Controller.
                                        In this case, there is only one instrument available.
    """

    number_available_modules: int = 1

    def _set_device_to_all_modules(self):
        """Sets the initialized device to the attached module.
        For a SingleInstrumentController, by default,
        the same controller device driver is set to the Instrument.
        """
        self.modules[0].device = self.device
