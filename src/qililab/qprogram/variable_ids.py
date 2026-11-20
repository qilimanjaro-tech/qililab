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
"""Variable ids made from any text, for the variables qililab creates itself."""

import re
from collections.abc import Container

from qprogram import RESERVED_KEYWORDS


def unique_variable_id(text: str, taken: Container[str]) -> str:
    """Turn ``text`` into a qprogram variable id that is not in ``taken``.

    A variable id is ``[A-Za-z_][A-Za-z0-9_]*`` and not a reserved ``.qp`` keyword. Every other character of ``text``
    becomes ``_``, a leading ``_`` is added when ``text`` does not start with a letter or ``_``, and ``_2``, ``_3``, ...
    is appended until the id is free.

    Args:
        text (str): The text, such as a label or a bus alias followed by a parameter.
        taken (Container[str]): The ids already used.

    Returns:
        str: The id.
    """
    # ASCII, as variable ids are: an accented letter becomes "_" too
    base = re.sub(r"\W", "_", text, flags=re.ASCII) or "variable"
    if not re.match(r"[A-Za-z_]", base):
        base = f"_{base}"
    candidate, suffix = base, 2
    while candidate in taken or candidate in RESERVED_KEYWORDS:
        candidate, suffix = f"{base}_{suffix}", suffix + 1
    return candidate
