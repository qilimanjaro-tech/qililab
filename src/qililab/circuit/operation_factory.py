from typing import Callable, Dict, Type


class OperationFactory:
    _operations: Dict[str, Type] = {}

    @classmethod
    def register(cls, operation: Type) -> Callable:
        def decorator(operation: Type) -> Type:
            cls._operations[operation.__name__] = operation
            return operation

        return decorator(operation=operation)

    @classmethod
    def get(cls, name: str) -> Type:
        if name in cls._operations:
            return cls._operations[name]
        else:
            raise ValueError(f"Operation '{name}' is not registered.")
