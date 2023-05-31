from qibo.gates.abstract import Gate, ParametrizedGate


class Reset(Gate):
    """The Reset operation.

    Args:
        q (int): the qubit id number.
    """

    def __init__(self, q):
        super().__init__()
        self.name = "reset"
        self.target_qubits = (q,)
        self.init_args = [q]


class Wait(ParametrizedGate):
    """The Reset operation.

    Args:
        q (int): the qubit id number.
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
