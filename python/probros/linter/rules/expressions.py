import ast

from diagnostic import Diagnostic

from .base_rule import BaseRule


class NoWalrusOperatorRule(BaseRule):

    message = "Walrus operators are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.NamedExpr)
            else None
        )


class NoFstringRule(BaseRule):

    message = "F-Strings are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.FormattedValue, ast.JoinedStr))
            else None
        )
