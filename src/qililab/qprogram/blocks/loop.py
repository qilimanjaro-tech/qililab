from dataclasses import dataclass

import numpy as np

from qililab.qprogram.blocks.block import Block
from qililab.qprogram.variable import Variable


@dataclass
class Loop(Block):
    variable: Variable
    values: np.ndarray
