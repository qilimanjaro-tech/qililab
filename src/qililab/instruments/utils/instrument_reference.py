""" Instrument Reference class. """

from dataclasses import dataclass


@dataclass
class InstrumentReference:
    """References an Instrument with its alias to be retrieved from the Instrument Factory.

    Args:
        alias (str): The alias name of the Instrument.
        slot_id (int): The number that identifies the slot used by the instrument within the
                            the possible list of available modules (i.e. on a Cluster).
    """

    alias: str
    slot_id: int  # slot_id represents the number displayed in the cluster

    def __iter__(self):
        """Iterate over InstrumentReference elements.

        Yields:
            tuple[tuple[str], tuple[str, int], tuple[str, int]]: alias and slot_id
        """
        yield from self.__dict__.items()

    def to_dict(self):
        """Return a dict representation of the InstrumentReference class."""
        return {"alias": self.alias, "slot_id": self.slot_id}

    @classmethod
    def from_dict(cls, settings: dict):
        """Build an InstrumentReference from a settings dictionary

        Args:
            settings (dict): an instrument reference from the settings file
        """
        return InstrumentReference(**settings)
