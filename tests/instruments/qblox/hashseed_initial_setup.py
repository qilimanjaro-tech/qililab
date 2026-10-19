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

"""Helper invoked as a subprocess by the QHC-1654 hash-seed tests.

It builds an RF module, runs ``initial_setup`` against a mocked device, and prints the ordered list of
``device.set`` parameter names as JSON. Running it under different ``PYTHONHASHSEED`` values must always
produce the same order. It is intentionally *not* named ``test_*`` so pytest does not collect it.

Usage: ``python hashseed_initial_setup.py {qcm|qrm} <runcard_path>``
"""

import json
import sys
from unittest.mock import MagicMock

from qililab.data_management import build_platform


def device_set_order(module: str, runcard: str) -> list[str]:
    """Return the parameter names passed to ``device.set`` during ``initial_setup``, in call order."""
    platform = build_platform(runcard=runcard)
    alias = "qcm-rf" if module == "qcm" else "qrm-rf"
    element = platform.get_element(alias=alias)

    element.device = MagicMock()
    # The attenuation branch of `set_parameter` compares against these, so they must be real numbers.
    element.device._get_max_out_att_0 = MagicMock(return_value=100)
    element.device._get_max_out_att_1 = MagicMock(return_value=100)
    element.device.sequencers = {0: MagicMock(), 1: MagicMock()}

    element.initial_setup()
    return [call.args[0] for call in element.device.set.call_args_list]


if __name__ == "__main__":
    print(json.dumps(device_set_order(sys.argv[1], sys.argv[2])))  # noqa: T201
