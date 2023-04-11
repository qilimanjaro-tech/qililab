from qibo.gates.abstract import Gate, ParametrizedGate


class RMW(ParametrizedGate):
    """
    Native drag pulse dummy
    """
    def __init__(self, q, theta, phi, trainable=True):
        super().__init__(q, trainable=trainable)
        self.name = "rmw"
        self.nparams = 2
        self._theta, self._phi = None, None
        self.init_kwargs = {"theta": theta, "phi": phi, "trainable": trainable}
        self.parameter_names = ["theta", "phi"]
        self.parameters = theta, phi



class CZ(Gate): # find out if CZ can be parametrized
    def __init__(self, q, theta, trainable=False): # FUTURE: trainable could be useful for fast setting gate parameters in var circuits via set_parameters in qibo
        super().__init__(q, theta, trainable)
        self.name = "cz"