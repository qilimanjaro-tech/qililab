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
from typing import TYPE_CHECKING, Any, Optional, Set, Type

if TYPE_CHECKING:
    from qilisdk.digital.gates import Gate
    from rustworkx import PyGraph


@dataclass
class TranspilationContext:
    """Shared, mutable state for passes."""
    # Artifacts produced/consumed by passes:
    initial_layout: Optional[list[int]] = None              # logical -> physical (from layout)
    final_layout: Optional[list[int]] = None                # (from router)
    metrics: dict[str, Any] = field(default_factory=dict)
