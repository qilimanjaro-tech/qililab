"""BusElement class"""
from dataclasses import asdict

from qililab.constants import YAML
from qililab.typings.enums import Parameter
from qililab.typings.factory_element import FactoryElement
from qililab.typings.settings import SettingsType
from qililab.utils import dict_factory


class BusElement(FactoryElement):
    """Class BusElement. All bus element classes must inherit from this class."""

    settings: SettingsType

    def set_parameter(self, parameter: Parameter | str, value: float | str | bool):
        """Redirect __setattr__ magic method."""
        if isinstance(parameter, Parameter):
            parameter = parameter.value
        self.settings.set_parameter(name=parameter, value=value)

    def to_dict(self):
        """Return a dict representation of the BusElement class."""
        return {YAML.NAME: self.name.value} | asdict(self.settings, dict_factory=dict_factory)
