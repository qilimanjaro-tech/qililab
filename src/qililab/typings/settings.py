"""SettingsType class."""


class SettingsType:
    """SettingsType class."""

    def set_parameter(self, name: str, value: float | str | bool):
        """Cast the new value to its corresponding type and set the new attribute."""
        attr_type = type(getattr(self, name))
        setattr(self, name, attr_type(value))
