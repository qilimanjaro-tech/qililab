from qibo.gates import Gate


class Park(Gate):
    """Parking gate qibo interface.
    Args:
        q (int): the qubit id number.
    """

    def __init__(self, q):
        super().__init__()
        self.name = "park"
        self.target_qubits = (q,)
        self.init_args = [q]
