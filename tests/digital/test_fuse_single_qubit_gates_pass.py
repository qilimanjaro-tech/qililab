import math
from typing import TYPE_CHECKING, List, Tuple

from qilisdk.digital import Circuit
from qilisdk.digital.gates import (
    CZ,
    RX,
    RY,
    RZ,
    SWAP,
    U3,
    Gate,
    M,
)

from qililab.digital.circuit_transpiler_passes.circuit_transpiler_pass import CircuitTranspilerPass
from qililab.digital.circuit_transpiler_passes.numeric_helpers import (
    _is_close_mod_2pi,
    _mat_RX,
    _mat_RY,
    _mat_RZ,
    _mat_U3,
    _wrap_angle,
    _zyz_from_unitary,
)

if TYPE_CHECKING:
    import numpy as np