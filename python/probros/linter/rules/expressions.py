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


class RestrictBinaryOperatorsRule(BaseRule):

    # Prohibit shift and bitwise operators.
    message = "Binary operators may only be of: +, -, *, /, //, %, **"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not isinstance(node, ast.BinOp):
            return None
        match node.op:
            case (
                ast.Add()
                | ast.Sub()
                | ast.Mult()
                | ast.Div()
                | ast.FloorDiv()
                | ast.Mod()
                | ast.Pow()
            ):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.BinOp)
            else None
        )


class RestrictUnaryOperatorsRule(BaseRule):

    # Prohibit the bitwise complement operator `~`.
    message = "Unary operators may only be of: +, -, not"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not isinstance(node, ast.UnaryOp):
            return None
        match node.op:
            case ast.UAdd() | ast.USub() | ast.Not():
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.BinOp)
            else None
        )


class NoLambdaRule(BaseRule):

    message = "Lambda expressions are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Lambda)
            else None
        )


class NoInlineIfRule(BaseRule):

    message = "Inline if expressions are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.IfExp)
            else None
        )


class NoDictionaryRule(BaseRule):

    message = "Dictionaries are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case ast.Dict() | ast.Call(func=ast.Name(id="dict")):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None


class NoFstringRule(BaseRule):

    message = "F-Strings are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.FormattedValue, ast.JoinedStr))
            else None
        )
