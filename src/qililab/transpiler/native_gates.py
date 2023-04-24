from qibo.gates.gates import _Un_


class Drag(_Un_):
    """Native drag pulse dummy class
    Inherits from qibo unitary gates class

    The native gate is a drag pulse
    .. math:: R_{MW}(\theta, \phi) = Z_\phi X_\theta Z_{-\phi}

    Together with virtual Z gates, this allows us to perform any single-qubit gate, since any
    such gate can be expressed as a unitary
    .. math:: U(\theta,\phi,\lambda) = Z_\phi X_\theta Z_\lambda    &= R_{MW}(\theta, \phi)Z_{\lambda+\phi} \\
                                                                    &= Z_{\phi+\lambda}R_{MW}(\theta, -\lambda)
    """

    def __init__(self, q: int, theta: float, phi: float, trainable: bool = False):
        """init method

        Args:
            q (int): qubit where the gate is applied
            theta (float): theta angle of rotation
            phi (float): phi angle of rotation
            trainable (bool): whether parameters are trainable (set to false)
        """
        super().__init__(q, trainable=trainable)
        self.name = "drag"
        self.nparams = 2
        self._theta, self._phi = None, None
        self.init_kwargs = {"theta": theta, "phi": phi, "trainable": trainable}
        self.parameter_names = ["theta", "phi"]
        self.parameters = theta, phi
