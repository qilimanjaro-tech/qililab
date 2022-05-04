"""BusesExecution class."""
from dataclasses import dataclass
from itertools import zip_longest
from typing import Dict, List

import numpy as np

from qililab.execution.bus_execution import BusExecution


@dataclass
class BusesExecution:
    """BusesExecution class."""

    buses: List[BusExecution]

    def connect(self):
        """Connect to the instruments."""
        for bus in self.buses:
            bus.connect()

    def setup(self):
        """Setup instruments with experiment settings."""
        for bus in self.buses:
            bus.setup()

    def start(self):
        """Start/Turn on the instruments."""
        for bus in self.buses:
            bus.start()

    def run(self):
        """Run the given pulse sequence."""
        results = []
        for bus in self.buses:
            result = bus.run()
            if result is not None:
                results.append(result)

        return results

    def close(self):
        """Close connection to the instruments."""
        for bus in self.buses:
            bus.close()

    def pulses(self, resolution: float = 1.0):
        """Get pulses of each bus and sum pulses by their qubit id.

        Args:
            resolution (float): The resolution of the pulses in ns.

        Returns:
            Dict[int, np.ndarray]: Dictionary containing a list of the I/Q amplitudes of the control and readout
            pulses applied on each qubit.
        """
        pulses: Dict[int, np.ndarray] = {}
        for bus in self.buses:
            new_pulses = np.array(bus.pulses(resolution=resolution))
            for qubit_id in bus.qubit_ids:
                if qubit_id not in pulses:
                    pulses[qubit_id] = new_pulses
                    continue
                old_pulses = pulses[qubit_id]
                pulses[qubit_id] = np.array(
                    [[x + y for x, y in zip_longest(old, new, fillvalue=0)] for old, new in zip(old_pulses, new_pulses)]
                )

        return pulses
