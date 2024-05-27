import ast

from diagnostic import Diagnostic

from .base_rule import BaseRule


class NoFstringRule(BaseRule):

    message = "F-Strings are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.FormattedValue, ast.JoinedStr))
            else None
        )
