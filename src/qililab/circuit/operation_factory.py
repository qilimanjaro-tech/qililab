"""OperationFactory class"""
from typing import Callable, Dict, Type


class OperationFactory:
    """A factory class to register and retrieve operation classes based on their names."""

    _operations: Dict[str, Type] = {}

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
        else:
            raise ValueError(f"Operation '{name}' is not registered.")
