# Copyright 2026 Qilimanjaro Quantum Tech
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

import enum
from typing import Final, Literal


class _Sentinel(enum.Enum):
    """Enum for sentinels in qililab. Enum members are what type checkers narrow
    on ``is`` / ``is not``. Add a member here plus its value and ``Literal`` alias below.
    """

    UNSET = enum.auto()

    def __repr__(self) -> str:
        return f"<{self.name}>"

Unset = Literal[_Sentinel.UNSET]
