"""
Emulator for the single qubit using the 2level approximation
"""

from typing import Any, Callable

from ..parameter import Parameter


class Qubit2LevelTranspiler:
    """Implementation of the transpiler for the 2 level qubit. This is done mainly by inverting the same functions
    used int he single_qubit_2level emulator model.

    Args:
        eps_model (Callable): epsilon model
        delta_model (Callable): delta model
        qubitData (DataClass): dataclass containing info about the physical parameters of the qubit. Defaults to None.
    """

    def __init__(self, epsilon_model: Callable, delta_model: Callable):
        """Init method. See class description for more details"""

        self.delta_model = delta_model
        self.epsilon_model = epsilon_model

        # Magnetic energy bias (epsilon)
        self.epsilon = Parameter(name="epsilon", set_method=self._set_epsilon)
        # Qubit gap (delta)
        self.delta = Parameter(name="delta", set_method=self._set_delta)
        # flux parameters
        self.phiz = Parameter(name="phiz")
        self.phix = Parameter(name="phix")

    def __call__(self, delta: float, epsilon: float) -> tuple[Any, Any]:
        """Transpiles Delta and Epsilon to phix, phiz"""
        self.delta(delta)
        self.epsilon(epsilon)
        return self.phix(), self.phiz()  # type: ignore[func-returns-value]

    def _set_delta(self, delta):
        # sets the value of delta via raw and updates phix accordingly
        phix = self.delta_model(delta, inverse=True)
        self.phix.set_raw(phix)
        return delta

    def _set_epsilon(self, epsilon):
        """sets the value of epsilon via raw and updates phiz accordingly. Does not update phix
        since this is meant to be used in the transpiler in conjunction with setting delta (which
        already updates phix)
        """
        self.phiz.set_raw(self.epsilon_model(phix=self.phix(), phiz_epsilon=epsilon, inverse=True))
        return epsilon
