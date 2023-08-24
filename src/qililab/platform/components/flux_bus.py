"""Driver for the Drive Bus class."""
from qililab.drivers.interfaces import AWG, CurrentSource, VoltageSource
from qililab.platform.components.bus_driver import BusDriver
from qililab.platform.components.bus_factory import BusFactory


@BusFactory.register
class FluxBus(BusDriver):
    """Qililab's driver for Flux Bus"""

    def __init__(self, alias: str, port: int, awg: AWG | None, source: CurrentSource | VoltageSource | None):
        """Initialise the bus.

        Args:
            alias: Bus alias
            port: Port to target
            awg (AWG): Bus awg instrument
            source (CurrentSource | VoltageSource): Bus source instrument
        """
        super().__init__(alias=alias, port=port, awg=awg)
        self.instruments["source"] = source

    def to_dict(self, instruments):
        """Generates a dict representation given the Buses and the instruments get_parms()"""
        raise NotImplementedError

    @classmethod
    def from_dict(cls, dictionary: dict) -> "FluxBus":
        """Generates the FluxBus class and passes the instrument params info to be set with set_params(), given a dictionary"""
        _ = dict
        raise NotImplementedError

    # @classmethod
    # def from_dict(cls, dictionary: dict) -> "FluxBus":
    #     """Load LFilterCorrection object from dictionary.

    #     Args:
    #         dictionary (dict): Dictionary representation of the LFilterCorrection object.

    #     Returns:
    #         LFilterCorrection: Loaded class.
    #     """
    #     local_dictionary = dictionary.copy()
    #     local_dictionary.pop(RUNCARD.NAME, None)
    #     return cls(**local_dictionary)

    # @abstractmethod
    # def to_dict(self) -> dict:
    #     """Return dictionary representation of the distortion.

    #     Returns:
    #         dict: Dictionary.
    #     """
    #     return {
    #         RUNCARD.NAME: self.name.value,
    #         PulseDistortionSettingsName.NORM_FACTOR.value: self.norm_factor,
    #         PulseDistortionSettingsName.A.value: self.a,
    #         PulseDistortionSettingsName.B.value: self.b,
    #     }
