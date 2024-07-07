""" This module contains rules for validating expression nodes.

Each rule is implemented as a class inheriting from `BaseRule`. Therefore, view
the documentation of that class in case of changes or additions.
"""

import ast

from diagnostic import Diagnostic

from .base import BaseRule

# Restrict operators. #########################################################


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


class RestrictComparisonOperatorsRule(BaseRule):

    # Prohibit `is`, `is not`, `in`, `not in`.
    message = (
        "Comparison operators may only be binary and one of: "
        "==, !=, <, <=, >, >="
    )

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not isinstance(node, ast.Compare):
            return None
        match node:
            case ast.Compare(
                ops=[
                    ast.Eq()
                    | ast.NotEq()
                    | ast.Lt()
                    | ast.LtE()
                    | ast.Gt()
                    | ast.GtE()
                ],
                comparators=comparators,
            ) if len(comparators) == 1:
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


# Prohibit inline statements. #################################################


class NoWalrusOperatorRule(BaseRule):

    message = "Walrus operators are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.NamedExpr)
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


# Restrict available data-structure. ##########################################


class NoDictionaryRule(BaseRule):

    message = "Dictionaries are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case ast.Dict() | ast.Call(func=ast.Name(id="dict")):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None


class NoSetRule(BaseRule):

    message = "Sets are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case ast.Set() | ast.Call(func=ast.Name(id="set")):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None


class NoComprehensionAndGeneratorRule(BaseRule):

    message = "Comprehensions are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(
                node,
                (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp),
            )
            else None
        )


# Restrict control flow constructs. ###########################################


class NoAsynchronousExpressionRule(BaseRule):

    message = "Asynchronous expressions are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case ast.Await():
                return Diagnostic.from_node(node, message=cls.message)
            case (
                ast.ListComp(generators=generators)
                | ast.SetComp(generators=generators)
                | ast.DictComp(generators=generators)
                | ast.GeneratorExp(generators=generators)
            ) if any(generator.is_async for generator in generators):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None


class NoYieldRule(BaseRule):

    message = "Yields are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.Yield, ast.YieldFrom))
            else None
        )


# Restrict syntax. ############################################################


class NoFstringRule(BaseRule):

    message = "F-Strings are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.JoinedStr)
            else None
        )


class NoStarredRule(BaseRule):

    message = "Starred variables are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Starred)
            else None
        )


# Restrict data-structure manipulation. #######################################


class NoSliceRule(BaseRule):

    message = "Slices are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Slice)
            else None
        )


class NoMultipleSubscriptRule(BaseRule):

    message = "Multi-subscripts are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Subscript)
            and isinstance(node.slice, (ast.List, ast.Tuple))
            else None
        )
