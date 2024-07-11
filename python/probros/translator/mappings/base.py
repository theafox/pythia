import ast
from abc import ABC, abstractmethod

from context import Context


class BaseMapping(ABC):
    @classmethod
    @abstractmethod
    def map(cls, node: ast.AST, context: Context) -> ast.AST | str:
        raise NotImplementedError("Mapping method not implemented.")
