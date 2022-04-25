from qililab.settings import ResonatorSettings


class Resonator:
    """Resonator class"""

    settings: ResonatorSettings

    def __init__(self, settings: dict):
        self.settings = ResonatorSettings(**settings)

    @property
    def id_(self):
        """Resonator 'id' property.

        Returns:
            int: settings.id_.
        """
        return self.settings.id_

    @property
    def name(self):
        """Resonator 'name' property.

        Returns:
            str: settings.name.
        """
        return self.settings.name

    @property
    def category(self):
        """Resonator 'category' property.

        Returns:
            str: settings.category.
        """
        return self.settings.category

    @property
    def qubits(self):
        """Resonator 'qubits' property.

        Returns:
            List[Qubit]: settings.qubits.
        """
        return self.settings.qubits
