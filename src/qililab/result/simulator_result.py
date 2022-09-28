"""SimulatorResult class."""
from dataclasses import dataclass

from qutip import Qobj

from qililab.result.result import Result
from qililab.typings.enums import ResultName
from qililab.utils.factory import Factory


@Factory.register
@dataclass
class SimulatorResult(Result):
    """SimulatorResult class.

    Stores results from the simulator.

    Attributes:
        - name (string): results type
        - psi0 (Qobj): initial state (at time t=0)
        - states (list[Qobj]): calculated states
        - times (list[float]): timestamp for each state, in s.

    Notes:
        - self.probabilities() is not implemented
    """

    name = ResultName.SIMULATOR

    psi0: Qobj
    states: list[Qobj]
    times: list[float]

    def probabilities(self) -> list[tuple[float, float]]:
        """Probabilities of being in the ground and excited state.

        Raises NotImplementedError.
        """
        return super().probabilities()
