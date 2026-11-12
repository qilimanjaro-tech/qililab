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
"""The block ``qp.infinite_loop()`` opens."""

from typing import ClassVar

from qprogram.blocks import Block


class InfiniteLoop(Block):
    """A body repeated until the instruments are stopped, from ``qp.infinite_loop()``.

    It re-runs its body, so it counts as a repetition level like a sweep (``REPEATS``). qililab owns
    it: in a ``.qp`` file it reads ``qililab.infinite_loop:``.
    """

    REPEATS: ClassVar[bool] = True

    def required_capabilities(self) -> set[str]:
        """Return the capability token of the block.

        Returns:
            set[str]: ``{"vendor.qililab.infinite_loop"}``.
        """
        return {"vendor.qililab.infinite_loop"}
