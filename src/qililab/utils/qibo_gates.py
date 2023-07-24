from qibo.gates.abstract import ParametrizedGate


class Wait(ParametrizedGate):
    """The Wait gate.

    Args:
        q (int): the qubit index.
        t (int): the time to wait (ns)
    """

    def __init__(self, q, t):
        super().__init__(trainable=True)
        self.name = "wait"
        self._controlled_gate = None
        self.target_qubits = (q,)

        self.parameters = t
        self.init_args = [q]
        self.init_kwargs = {"t": t}
