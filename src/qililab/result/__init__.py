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

"""This module contains the classes used to return the results of the execution of a program.

.. currentmodule:: qililab

Classes
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Results
    ~result.Result

Functions
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~stream_results
"""

from .result import Result
from .results import Results
from .stream_results import stream_results

__all__ = ["Result", "Results", "stream_results"]
