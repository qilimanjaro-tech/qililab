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
    def id_(self):
        """Bus 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Bus 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Bus 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def elements(self):
        """Bus 'elements' property.

        Returns:
            List[QubitControl | QubitReadout | SignalGenerator | Mixer | Resonator]: settings.elements.
        """
        return self.settings.elements

    @property
    def signal_generator(self):
        """Bus 'signal_generator' property.

        Returns:
            SignalGenerator: settings.signal_generator.
        """
        return self.settings.signal_generator

    @property
    def mixer(self):
        """Bus 'mixer' property.

        Returns:
            Mixer: settings.mixer.
        """
        return self.settings.mixer

    @property
    def resonator(self):
        """Bus 'resonator' property.

        Returns:
            Resonator: settings.resonator.
        """
        return self.settings.resonator

    @property
    def qubit_control(self):
        """Bus 'qubit_control' property.

        Returns:
            (QubitControl | None): settings.qubit_control.
        """
        return self.settings.qubit_control

    @property
    def qubit_readout(self):
        """Bus 'qubit_readout' property.

        Returns:
            (QubitReadout | None): settings.qubit_readout.
        """
        return self.settings.qubit_readout

    def __iter__(self):
        """Redirect __iter__ magic method to iterate over bus elements."""
        return self.settings.__iter__()
