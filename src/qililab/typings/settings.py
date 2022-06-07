"""SettingsType class."""


class SettingsType:
    """SettingsType class."""

    def set_parameter(self, name: str, value: float | str | bool):
        """Cast the new value to its corresponding type and set the new attribute."""
        attr_type = type(getattr(self, name))
        if attr_type == int:  # FIXME: Depending on how we define de value, python thinks it is an int
            attr_type = float
        setattr(self, name, attr_type(value))
