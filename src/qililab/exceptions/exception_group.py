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

import sys

# For Python 3.11+, we use ExceptionGroup; otherwise, we define a custom exception class
if sys.version_info >= (3, 11):  # pragma: no cover
    # Available natively in Python 3.11+
    from builtins import ExceptionGroup
else:
    # Define a custom exception class for earlier versions
    class ExceptionGroup(Exception):
        """Custom implementation of ExceptionGroup."""

        def __init__(self, message, exceptions):
            self.exceptions = exceptions
            super().__init__(f"{message}: {', '.join(str(e) for e in exceptions)}")
