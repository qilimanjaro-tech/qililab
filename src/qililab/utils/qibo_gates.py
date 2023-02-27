from qibo.gates.abstract import Gate, ParametrizedGate


class Reset(Gate):
    def __init__(self, q):
        super().__init__()
        self.name = "reset"
        self.target_qubits = (q,)
        self.init_args = [q]


class Wait(ParametrizedGate):
    def __init__(self, q, n):
        super().__init__(trainable=True)
        self.name = "wait"
        self._controlled_gate = None
        self.target_qubits = (q,)

        self.parameters = n
        self.init_args = [q]
        self.init_kwargs = {"n": n}
