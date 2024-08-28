import ast
from abc import ABC, abstractmethod
from typing import Any

from context import Context


class BaseMapping(ABC):
    @classmethod
    @abstractmethod
    def map(cls, node: ast.AST, context: Context) -> str:
        raise NotImplementedError("Mapping method not implemented.")


class MappingError(Exception):
    def __init__(
        self,
        message: str = "An error occured during translation.",
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(message, *args, **kwargs)
        self.message = message
