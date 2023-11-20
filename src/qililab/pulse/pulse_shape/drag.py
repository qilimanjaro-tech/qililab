# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Drag pulse shape."""
from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


# pylint: disable=anomalous-backslash-in-string
@Factory.register
@dataclass(frozen=True, eq=True)
class Drag(PulseShape):
    """Derivative Removal by Adiabatic Gate (DRAG) pulse shape. Standard Gaussian pulse with an additional Gaussian derivative component.

    It is designed to reduce the frequency spectrum of a normal gaussian pulse near the :math:`|1> - |2>` transition, reducing the chance of leakage to the :math:`|2>` state:

    .. math::

        f(x) & = (1 + 1j * alpha * d/dx) * Gaussian(x) = \\\\
             & = (1 + 1j * alpha * (x - \mu) / \sigma^2) * Gaussian(x)

    where the 'Gaussian' is symmetrically cut in the given `num_sigmas`, and then is shifted down so that the extremes are at 0, following:

    .. math::

        Gaussian(x) = A * exp(-0.5 * (x - \mu)^2 / \sigma^2)

    more information about the gaussian can be found in the :class:`Gaussian` documentation.

    Examples:
        To get the envelope of a drag shape, with ``num_sigmas = 8`` and ``drag_coefficient`` (`alpha`) equal to ``X``, you need to do:

        .. code-block:: python

            from qililab.pulse.pulse_shape import Drag
            rectangular_envelope = Drag(num_sigmas=8, drag_coefficient=X).envelope(amplitude=1., duration=50)

        which for ``X`` being ``1`` and ``10``, look respectively like:

        .. image:: /classes_images/drags.png
            :width: 800
            :align: center

    References:
        - Analytic control methods for high-fidelity unitary operations in a weakly nonlinear oscillator: https://journals.aps.org/pra/abstract/10.1103/PhysRevA.83.012308.
        - Simple Pulses for Elimination of Leakage in Weakly Nonlinear Qubits: https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.103.110501.

    Args:
        num_sigmas (float): Sigma number of the gaussian pulse shape. Defines the width of the gaussian pulse.
        drag_coefficient (float): Drag coefficient that gives the DRAG its imaginary components.
    """

    name = PulseShapeName.DRAG  #: Name of the drag pulse shape.
    num_sigmas: float
    drag_coefficient: float

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """DRAG envelope centered with respect to the pulse.

        The first point of the gaussian in the envelope is shifted to avoid introducing noise at time 0.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            resolution (float, optional): Resolution of the pulse. Defaults to 1.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        sigma = duration / self.num_sigmas
        time = np.arange(duration / resolution) * resolution
        mu_ = duration / 2

        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        norm = np.amax(np.abs(np.real(gaussian)))

        gaussian = gaussian - gaussian[0]  # Shift to avoid introducing noise at time 0
        corr_norm = np.amax(np.abs(np.real(gaussian)))

        drag_gaussian = (1 - 1j * self.drag_coefficient * (time - mu_) / sigma**2) * gaussian

        return drag_gaussian * norm / corr_norm if corr_norm != 0 else drag_gaussian

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Drag":
        """Loads Drag object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Drag object/shape containing the name of the pulse shape, the
            number of sigmas and the drag coefficient.

        Returns:
            Drag: Loaded class.
        """
        local_dictionary = deepcopy(dictionary)
        local_dictionary.pop("name", None)
        return cls(**local_dictionary)

    def to_dict(self) -> dict:
        """Returns dictionary representation of the Drag object/shape.

        Returns:
            dict: Dictionary representing the Drag pulse shape. It contains the name of the pulse shape, the number of sigmas and
            the drag coefficient.
        """
        return {
            "name": self.name.value,
            "num_sigmas": self.num_sigmas,
            "drag_coefficient": self.drag_coefficient,
        }
