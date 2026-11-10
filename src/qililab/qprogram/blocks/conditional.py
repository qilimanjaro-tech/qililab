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
"""The block ``qp.if_trigger()`` opens."""

from qprogram.blocks import Block


class IfTrigger(Block):
    """Block whose elements only execute if the external trigger was received in time, from ``qp.if_trigger()``.

    qililab owns it: in a ``.qp`` file it reads ``qililab.if_trigger:``. It is not qprogram's
    ``Conditional``, which branches on a measured state.

    Args:
        trigger_padding_ns (int | None, optional): Extra wait, in ns, before checking the trigger. Defaults to None.
        expected_wait_time_ns (int | None, optional): The trigger period, in ns. Defaults to None.
    """

    def __init__(self, trigger_padding_ns: int | None = None, expected_wait_time_ns: int | None = None) -> None:
        super().__init__()
        self.trigger_padding_ns = trigger_padding_ns
        self.expected_wait_time_ns = expected_wait_time_ns

    def required_capabilities(self) -> set[str]:
        """Return the capability token of the block.

        Returns:
            set[str]: ``{"vendor.qililab.if_trigger"}``.
        """
        return {"vendor.qililab.if_trigger"}
