from qibo.gates.gates import _Un_


class Drag(_Un_):
    """Native drag pulse dummy class
    Inherits from qibo unitary gates class
    """

    def __init__(self, q, theta, phi, trainable=False):
        """init method

        Args:
            q (int): qubit where the gate is applied
            theta (float): theta angle of rotation
            phi (float): phi angle of rotation
            trainable (bool): whether parameters are trainable (set to false)
        """
        super().__init__(q, trainable=trainable)
        self.name = "drag"  # TODO change name, check that it does not break other functions
        self.nparams = 2
        self._theta, self._phi = None, None
        self.init_kwargs = {"theta": theta, "phi": phi, "trainable": trainable}
        self.parameter_names = ["theta", "phi"]
        self.parameters = theta, phi
