""" Execution Typings """

from dataclasses import asdict, dataclass, field

from qililab.typings.yaml_type import yaml


@dataclass
class ExecutionOptions:
    """Execution Options"""

    set_initial_setup: bool = field(default=False)
    automatic_connect_to_instruments: bool = field(default=True)
    automatic_disconnect_to_instruments: bool = field(default=True)
    automatic_turn_on_instruments: bool = field(default=False)
    automatic_turn_off_instruments: bool = field(default=False)

    def __str__(self):
        """Returns a string representation of the execution otions."""
        return yaml.dump(asdict(self), sort_keys=False)
