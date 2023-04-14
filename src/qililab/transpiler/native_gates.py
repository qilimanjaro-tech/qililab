from qibo.gates.abstract import Gate, ParametrizedGate
from qibo.gates.gates import _Un_


class RMW(_Un_):
    """
    Native drag pulse dummy
    """

    def __init__(self, q, theta, phi, trainable=False):
        super().__init__(q, trainable=trainable)
        self.name = "rmw"
        self.nparams = 2
        self._theta, self._phi = None, None
        self.init_kwargs = {"theta": theta, "phi": phi, "trainable": trainable}
        self.parameter_names = ["theta", "phi"]
        self.parameters = theta, phi
