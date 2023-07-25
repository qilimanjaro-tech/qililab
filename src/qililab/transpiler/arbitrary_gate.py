from qibo.gates import Gate


class Arbitrary(Gate):
    """Arbitrary gate qibo interface.
    Args:
        q (int): the qubit id number.
    """

    def __init__(self, q):
        super().__init__()
        self.name = "arbitrary"
        self.target_qubits = (q,)
        self.init_args = [q]
