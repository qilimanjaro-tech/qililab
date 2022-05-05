"""Schema class"""
from dataclasses import InitVar, dataclass
from typing import List

from qililab.constants import YAML
from qililab.platform.components.bus_control import BusControl
from qililab.platform.components.bus_readout import BusReadout
from qililab.platform.components.buses import Buses
from qililab.typings import Category, SchemaDrawOptions


@dataclass
class Schema:
    """Class representing the schema of the platform.

    Args:
        settings (SchemaSettings): Settings that define the schema of the platform.
    """

    elements: InitVar[List[dict]]

    def __post_init__(self, elements: List[dict]):
        """Cast each list element to its corresponding bus class and instantiate class Buses."""
        buses: List[BusControl | BusReadout] = []
        for bus in elements:
            if bus[YAML.READOUT] is False:
                buses.append(BusControl(**bus))
            elif bus[YAML.READOUT] is True:
                buses.append(BusReadout(**bus))
            else:
                raise ValueError("Bus 'readout' key should contain a boolean.")

        self.buses = Buses(buses=buses)

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
                for _, element in bus:
                    print(f"|{element.name}", end="|------")
                print()
        elif options == SchemaDrawOptions.FILE:
            raise NotImplementedError("This function is not implemented yet.")
