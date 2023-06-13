""" AWG Sequencer """
from dataclasses import asdict, dataclass

from qililab.config import logger
from qililab.utils.asdict_factory import dict_factory


@dataclass
class Sequencer:
    """AWG Sequencer

    Args:
        identifier (int): The identifier of the sequencer
        chip_port_id (int | None): Port identifier of the chip where a specific sequencer is connected to.
                                    By default, using the first sequencer
        output_i (int): AWG output associated with the I channel of the sequencer
        output_q (int): AWG output associated with the Q channel of the sequencer
        intermediate_frequency (float): Frequency for each sequencer
        gain_imbalance (float): Amplitude added to the Q channel.
        phase_imbalance (float): Dephasing.
        hardware_modulation  (bool): Flag to determine if the modulation is performed by the device
        gain_i (float): Gain step used by the I channel of the sequencer.
        gain_q (float): Gain step used by the Q channel of the sequencer.
        offset_i (float): I offset (unitless). amplitude + offset should be in range [0 to 1].
        offset_q (float): Q offset (unitless). amplitude + offset should be in range [0 to 1].
    """

    identifier: int
    chip_port_id: int
    parameters: dict[str, float | int | str]

    def __post_init__(self):
        output_i = self.parameters.get("output_i")
        output_q = self.parameters.get("output_q")
        if output_i in {0, 2, None} and output_q in {1, 3, None}:
            self.path_i = 0
            self.path_q = 1
        elif output_i in {1, 3, None} and output_q in {0, 2, None}:
            logger.warning(
                "Cannot set `output_i=%i` and `output_q=%i` in hardware. The I/Q signals sent to sequencer %i will "
                "be swapped to allow this setting.",
                output_i,
                output_q,
                self.identifier,
            )
            self.path_i = 1
            self.path_q = 0
        else:
            raise ValueError(
                f"Cannot map both paths of sequencer {self.identifier} into an even/odd output."
                f" Obtained `output_i={output_i}` and `output_q={output_q}`."
            )

    def to_dict(self):
        """Return a dict representation of an AWG Sequencer."""
        output_i = self.parameters.get("output_i")
        output_q = self.parameters.get("output_q")
        dictionary = asdict(self, dict_factory=dict_factory) | {"output_i": output_i, "output_q": output_q}
        # Remove values not present in the __init__ function
        dictionary.pop("path_i")
        dictionary.pop("path_q")
        return dictionary
