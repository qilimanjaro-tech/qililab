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

    def probabilities(self) -> dict[str, float]:
        """Probabilities of being in the ground and excited state.

        Returns arbitrary result.
        """
        # FIXME: need bypass when this is not implemented
        n_qubits = len(self.states)
        avg_probability = 1.0 / (2**n_qubits)
        return {bin(i)[2:].zfill(n_qubits): avg_probability for i in range(2**n_qubits)}

    def to_dict(self) -> dict:
        """Returns dict with class data.

        Notes:
            - Since Qobj is returned as object, PyYAML complains.
        """
        # FIXME: yaml.safe_dump fails with default implementation
        return {}
