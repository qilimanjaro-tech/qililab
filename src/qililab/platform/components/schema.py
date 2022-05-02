"""Schema class"""
from dataclasses import dataclass
from typing import List

from qililab.platform.components.buses import Buses
from qililab.typings import Category, SchemaDrawOptions


@dataclass
class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
    """

    buses: Buses

    def get_element(self, category: Category, id_: int):
        """Get buses element. Return None if element is not found.

        Args:
            category (str): Category of element.
            id_ (int): ID of element.

        Returns:
            Tuple[(Qubit | QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator | None), List]: Tuple
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
                for element in bus:
                    print(f"|{element.name}", end="|------")
                print()
        elif options == SchemaDrawOptions.FILE:
            raise NotImplementedError("This function is not implemented yet.")

    def to_dict(self):
        """Return a dict representation of the SchemaSettings class."""
        return {
            "buses": [bus.to_dict() for bus in self.buses],
        }
