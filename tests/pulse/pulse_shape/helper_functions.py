""" Module containging new helper functions for envelopes."""
import numpy as np

from qililab.pulse.pulse_shape import PulseShape


def return_envelope(pulse_shape: PulseShape, env_params: dict[str, int]) -> list[np.ndarray]:
    """Function that generates the envelopes for the tests."""
    return pulse_shape.envelope(
        duration=env_params["duration"],
        amplitude=env_params["amplitude"],
        resolution=env_params["resolution"],
    )
