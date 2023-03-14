"""Dictionary class with a pretty print."""
import yaml


class PrettyDict(dict):
    """Dictionary class that uses YAML to print a more visual version of its data."""

    def __repr__(self):
        """Returns a pretty representation of the dictionary.

        Returns:
            str: dictionary representation
        """
        return str(yaml.dump(dict(self), sort_keys=False))
