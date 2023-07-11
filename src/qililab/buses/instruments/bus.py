"""Driver for the Drive Bus class."""
from qcodes.instrument.channel import ChannelTuple, InstrumentModule
from qcodes.metadatable import Metadatable

class GenericBus():
    """Qililab's driver for Drive Bus"""

    def __init__(self, **kwargs):
        """Initialise the bus.

        Args:
            name (str): Sequencer name
            address (str): Instrument address
        """
        self.submodules: dict[str, InstrumentModule | ChannelTuple] = {}

    def add_submodule(
        self, name: str, submodule: InstrumentModule | ChannelTuple
    ) -> None:
        """
        Bind one submodule to this bus.

        Args:
            name: How the submodule will be stored within
                ``bus.submodules`` and also how it can be
                addressed.
            submodule: The submodule to be stored.

        Raises:
            KeyError: If this instrument already contains a submodule with this
                name.
            TypeError: If the submodule that we are trying to add is
                not an instance of an ``Metadatable`` object.
        """
        if name in self.submodules:
            raise KeyError(f"Duplicate submodule name {name}")
        if not isinstance(submodule, Metadatable):
            raise TypeError("Submodules must be metadatable.")
        self.submodules[name] = submodule
