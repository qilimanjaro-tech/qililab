"""Schema class"""
from typing import List

from qililab.constants import YAML
from qililab.instruments import Instrument, InstrumentFactory, Instruments
from qililab.platform.components.bus import Bus
from qililab.platform.components.buses import Buses
from qililab.typings import Category, SchemaDrawOptions


class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
    """

    def __init__(self, buses: List[dict], instruments: List[dict]):
        """Cast each list element to its corresponding bus class and instantiate class Buses."""
        self.instruments = Instruments(elements=self._load_instruments(instruments_dict=instruments))
        self.buses = Buses(elements=[Bus(settings=bus, instruments=self.instruments) for bus in buses])

    def get_element(self, category: Category, id_: int):
        """Get buses element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            Tuple[(Qubit | QubitControl | QubitReadout | SignalGenerator | Resonator | None), List]: Tuple
            containing the element object and a list of the bus indeces where the element is located.
        """
        element = None
        bus_idxs: List[int] = []
        for bus_idx, bus in enumerate(self.buses):
            element_tmp = bus.get_element(category=category, id_=id_)
            if element_tmp is not None:
                # assert element == element_tmp
                element = element_tmp
                bus_idxs.append(bus_idx)
        return element, bus_idxs

    def draw(self, options: SchemaDrawOptions) -> None:
        """Draw schema.

        Args:
            options (SchemaDrawOptions): Method to generate the drawing.
        """
        if options == SchemaDrawOptions.PRINT:
            for idx, bus in enumerate(self.buses):
                print(f"Bus {idx}:\t", end="------")
                for _, element in bus:
                    print(f"|{element.name}", end="|------")
                print()
        elif options == SchemaDrawOptions.FILE:
            raise NotImplementedError("This function is not implemented yet.")

    def _load_instruments(self, instruments_dict: List[dict]) -> List[Instrument]:
        """Instantiate all instrument classes from their respective dictionaries.

        Args:
            instruments_dict (List[dict]): List of dictionaries containing the settings of each instrument.

        Returns:
            List[Instrument]: List of instantiated instrument classes.
        """
        instruments: List[Instrument] = []
        for instrument in instruments_dict:
            dict_name = instrument.pop(YAML.NAME)
            instruments.append(InstrumentFactory.get(dict_name)(settings=instrument))
        return instruments

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {"buses": self.buses.to_dict(), "instruments": self.instruments.to_dict()}
