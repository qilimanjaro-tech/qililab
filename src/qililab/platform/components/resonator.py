from qililab.settings import ResonatorSettings


class Resonator:
    """Resonator class"""

    settings: ResonatorSettings

    def __init__(self, settings: dict):
        self.settings = ResonatorSettings(**settings)
