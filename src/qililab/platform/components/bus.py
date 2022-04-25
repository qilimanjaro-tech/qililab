from dataclasses import dataclass

from qililab.settings.platform.components.bus import BusSettings


@dataclass
class Bus:
    """Bus class. Ideally a bus should contain a qubit control/readout and a signal generator, which are connected
    through a mixer for up- or down-conversion. At the end/beginning of the bus there should be a resonator object, which
    is connected to one or multiple qubits.

    Args:
        settings (BusSettings): Bus settings.
    """

    settings: BusSettings

    @property
    def elements(self):
        """Bus 'elements' property.

        Returns:
            List[QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator]: Return list of elements in bus.
        """
        return self.settings.elements

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.

        Returns:
            SignalGenerator: Return SignalGenerator object.
        """
        return self.settings.signal_generator

    @property
    def mixer(self):
        """Bus 'mixer' property.

        Returns:
            Mixer: Return Mixer object.
        """
        return self.settings.mixer

    @property
    def resonator(self):
        """Bus 'resonator' property.

        Returns:
            Resonator: Return Resonator object.
        """
        return self.settings.resonator

    @property
    def qubit_control(self):
        """Bus 'qubit_control' property.

        Returns:
            (QubitControl | None): Return QubitControl object. Return None if bus doesn't have any qubit control.
        """
        return self.settings.qubit_control

    @property
    def qubit_readout(self):
        """Bus 'qubit_readout' property.

        Returns:
            (QubitReadout | None): Return QubitReadout object. Return None if bus doesn't have any qubit readout.
        """
        return self.settings.qubit_readout

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over bus elements."""
        return self.settings.__iter__()
