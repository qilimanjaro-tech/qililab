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
"""The blocks qililab adds to qprogram's, and the point count of the deprecated ``qp.for_loop``."""

from .conditional import IfTrigger
from .for_loop import ForLoop, for_loop_iterations, to_scalar
from .infinite_loop import InfiniteLoop
from .loop_variables import reject_variables_swept_by_enclosing_loops, swept_variables

__all__ = [
    "ForLoop",
    "IfTrigger",
    "InfiniteLoop",
    "for_loop_iterations",
    "reject_variables_swept_by_enclosing_loops",
    "swept_variables",
    "to_scalar",
]
