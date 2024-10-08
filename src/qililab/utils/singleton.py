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

"""Singleton classes."""

from abc import ABCMeta
from typing import ClassVar


class Singleton(type):
    """Singleton metaclass used to limit to 1 the number of instances of a subclass."""

    _instances: ClassVar[dict] = {}

    def __call__(cls, *args, **kwargs):
        """Create a new instance of cls if it doesn't already exist."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonABC(ABCMeta):
    """ABC singleton metaclass used to limit to 1 the number of instances of a subclass."""

    _instances: ClassVar[dict] = {}

    def __call__(cls, *args, **kwargs):
        """Create a new instance of cls if it doesn't already exist."""
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonABC, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
