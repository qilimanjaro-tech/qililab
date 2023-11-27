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

"""
This is the top level module from which all basic functions and classes of
Qililab can be directly imported.
"""

# isort: skip_file
import contextlib

from .about import about
from .config import __version__, logger
from .data_management import build_platform, load_results, save_platform, save_results
from .execute_circuit import execute
from .experiment import Experiment
from .qprogram import Domain, QbloxCompiler, QProgram, QuantumMachinesCompiler
from .result import Results, stream_results
from .typings import ExperimentOptions, ExperimentSettings, Parameter
from .utils import Loop
from .utils.load_data import load
from .waveforms import *

# moving circuit_transpiler module imports here because it has instruments module dependencies so circular imports can be avoided
from .circuit_transpiler import Drag, Wait

with contextlib.suppress(NameError, ImportError):
    # Since Ipython magic methods can only be imported from inside a Jupyter Notebook,
    # here we first check that `get_ipython` exists (which means we are inside a Jupyter Notebook)
    get_ipython()  # type: ignore  # noqa: F405 # pylint: disable=undefined-variable
    from .slurm import submit_job  # pragma: no cover
