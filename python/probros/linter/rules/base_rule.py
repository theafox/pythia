import ast
from abc import ABC, abstractmethod

from diagnostic import Diagnostic


class BaseRule(ABC):

    message: str

    @classmethod
    @abstractmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        raise NotImplementedError("Subclasses must implement this.")
