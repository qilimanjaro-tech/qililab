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

"""OperationFactory class"""
from typing import Callable, Type


class OperationFactory:
    """A factory class to register and retrieve operation classes based on their names."""

    _operations: dict[str, Type] = {}

    @classmethod
    def register(cls, operation: Type) -> Callable:
        """Registers an operation class to the factory.

        Args:
            operation (Type): The operation class to be registered.

        Returns:
            Callable: A decorator that registers the operation class to the factory.
        """

        def decorator(operation: Type) -> Type:
            cls._operations[operation.name.value] = operation
            return operation

        return decorator(operation=operation)

    @classmethod
    def get(cls, name: str) -> Type:
        """Retrieves the operation class registered with the given name.

        Args:
            name (str): The name of the operation class to retrieve.

        Returns:
            Type: The operation class registered with the given name.

        Raises:
            ValueError: If the operation class with the given name is not registered.
        """
        if name in cls._operations:
            return cls._operations[name]
        raise ValueError(f"Operation '{name}' is not registered.")
