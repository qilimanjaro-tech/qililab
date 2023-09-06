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

from __future__ import annotations

from dataclasses import dataclass, field

from qililab.qprogram.element import Element
from qililab.qprogram.operations.operation import Operation


@dataclass(frozen=True)
class Block(Element):  # pylint: disable=missing-class-docstring
    elements: list[Block | Operation] = field(default_factory=list, init=False)

    def append(self, element: Block | Operation):  # pylint: disable=missing-function-docstring
        self.elements.append(element)
