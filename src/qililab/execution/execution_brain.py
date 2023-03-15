"""ExecutionManager class."""
from dataclasses import dataclass, field
from pathlib import Path
from threading import Thread
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

from qililab.circuit import Circuit
from qililab.config import logger
from qililab.constants import RESULTSDATAFRAME
from qililab.execution.execution_buses import (
    PulseScheduledBus,
    PulseScheduledReadoutBus,
)
from qililab.platform.components.bus_types import ContinuousBus
from qililab.result import Result
from qililab.typings import yaml
from qililab.utils import LivePlot, Waveforms


@dataclass
class ExecutionBrain:
    """ExecutionBrain class."""
