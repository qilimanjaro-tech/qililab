# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Top level module from which all Qililab basic functions and classes can be directly imported."""

# isort: skip_file
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("qililab")
except PackageNotFoundError:
    __version__ = "0.0.0"

import contextlib

from .about import about
from .config import logger
from .data_management import build_platform, save_platform
from .execute_circuit import execute
from .qprogram import Calibration, CrosstalkMatrix, Domain, QProgram, Experiment
from .platform import Platform
from .result import ExperimentResults, load_by_id, stream_results
from .typings import Parameter
from .utils.serialization import serialize, serialize_to, deserialize, deserialize_from
from .waveforms import (
    IQPair,
    SuddenNetZero,
    Square,
    Gaussian,
    FlatTop,
    Arbitrary,
    DragCorrection,
    Waveform,
    Ramp,
    Chained,
)

# moving circuit_transpiler module imports here because it has instruments module dependencies so circular imports can be avoided
from .digital import Drag, Wait
from .analog import AnnealingProgram  # same as circuit transpiler, top modules should be imported at top
from .result import Cooldown, DatabaseManager, Sample, get_db_manager, load_results, save_results, Measurement
from .qililab_settings import get_settings

__all__ = [
    "AnnealingProgram",
    "Arbitrary",
    "Calibration",
    "Chained",
    "Cooldown",
    "CrosstalkMatrix",
    "DatabaseManager",
    "Domain",
    "Drag",
    "DragCorrection",
    "Experiment",
    "ExperimentResults",
    "FlatTop",
    "Gaussian",
    "IQPair",
    "Measurement",
    "Parameter",
    "Platform",
    "QProgram",
    "Ramp",
    "Sample",
    "Square",
    "SuddenNetZero",
    "Wait",
    "Waveform",
    "__version__",
    "about",
    "build_platform",
    "deserialize",
    "deserialize_from",
    "execute",
    "get_db_manager",
    "get_settings",
    "load_by_id",
    "load_results",
    "logger",
    "save_platform",
    "save_results",
    "serialize",
    "serialize_to",
    "stream_results",
]


with contextlib.suppress(NameError, ImportError):
    # Since Ipython magic methods can only be imported from inside a Jupyter Notebook,
    # here we first check that `get_ipython` exists (which means we are inside a Jupyter Notebook)
    get_ipython()  # type: ignore  # noqa: F821
    from .slurm import submit_job as submit_job  # pragma: no cover
