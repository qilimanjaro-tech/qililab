from dataclasses import dataclass


@dataclass
class Settings:
    """Class containing the settings loaded from a yaml file"""

    def __init__(self, settings: dict) -> None:
        """Build an attribute for each element in settings

        Args:
            settings (dict): Dictionary containing the settings of a yaml file
        """
        for key, value in settings.items():
            setattr(self, key, value)

    # TODO: Add method to save values into yaml, which will use the asdict method.
    def asdict(self) -> dict:
        """Represent class as a dictionary

        Returns:
            dict: Dictionary containing all the settings
        """
        # FIXME: Should we keep this copy for safety issues, or not?
        return self.__dict__.copy()
