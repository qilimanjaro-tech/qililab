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

from dataclasses import asdict, dataclass


@dataclass
class FluxControlTopology:
    """Dataclass fluxes (e.g. phix_q0 for phix control of qubit 0) and their corresponding bus (e.g. flux_line_q0_x)"""

    flux: str
    bus: str

    def to_dict(self):
        """Method to convert to dictionary"""
        return asdict(self)
