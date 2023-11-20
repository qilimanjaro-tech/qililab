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

""" Qblox Scope Data """

from dataclasses import dataclass


@dataclass
class ScopeData:
    """Scope data."""

    @dataclass
    class PathData:
        """Path data."""

        data: list[float]
        avg_cnt: int
        out_of_range: bool

    path0: PathData
    path1: PathData

    def __post_init__(self):
        """Change invalid name and cast to PathData class."""
        if isinstance(self.path0, dict) and isinstance(self.path1, dict):
            if "out-of-range" in self.path0:  # pylint: disable=unsupported-membership-test
                self.path0["out_of_range"] = self.path0.pop("out-of-range")
            self.path0 = self.PathData(**self.path0)  # pylint: disable=not-a-mapping
            if "out-of-range" in self.path1:  # pylint: disable=unsupported-membership-test
                self.path1["out_of_range"] = self.path1.pop("out-of-range")
            self.path1 = self.PathData(**self.path1)  # pylint: disable=not-a-mapping
