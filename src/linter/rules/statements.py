"""This module contains rules for validating statement nodes.

Each rule is implemented as a class inheriting from `BaseRule`. Therefore, view
the documentation of that class in case of changes or additions.
"""

import ast
from typing import override

from linter import Diagnostic, Severity

from .base import BaseRule
from .utils import is_function_called

# Prohibit nested definitions and imports. ####################################


class NoNestedFunctionsRule(BaseRule):
    message = "Nested functions are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            else None
        )


class NoNestedClassesRule(BaseRule):
    message = "Nested classes are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.ClassDef)
            else None
        )


class NoImportRule(BaseRule):
    message = "Importing is prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            else None
        )


class NoGlobalOrNonlocalDeclarationRule(BaseRule):
    message = "Declaring global variables is prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.Global, ast.Nonlocal))
            else None
        )


# Restrict variable manipulations. ############################################


class NoDeleteStatementRule(BaseRule):
    message = "Delete statements are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Delete)
            else None
        )


class NoTypeAliasRule(BaseRule):
    message = "Type aliasing is prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.TypeAlias)
            else None
        )


class NoDeconstructorRule(BaseRule):
    message = "Deconstructors are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        # Deconstruction can only occur on `Assign`, `AnnAssign` (annotated
        # assign) and `AugAssign` (augmented assign) cannot use deconstructors.
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, (ast.Tuple, ast.List))
                for target in node.targets
            )
            else None
        )


class NoChainedAssignmentRule(BaseRule):
    message = "Chained assignments are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Assign) and len(node.targets) > 1
            else None
        )


class NoAugmentedAssignRule(BaseRule):
    message = "Augmented assigns are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.AugAssign)
            else None
        )


class WarnAnnotatedAssignRule(BaseRule):
    message = "Annotated assigns are discouraged"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(
                node,
                message=cls.message,
                severity=Severity.WARNING,
            )
            if isinstance(node, ast.AnnAssign)
            else None
        )


class NoAttributeAssignRule(BaseRule):
    message = "Attributes may not be written to"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case ast.Assign(targets=targets) if any(
                isinstance(target, ast.Attribute) for target in targets
            ):
                return Diagnostic.from_node(node, message=cls.message)
            case (
                ast.AnnAssign(target=ast.Attribute())
                | ast.AugAssign(target=ast.Attribute())
            ):
                return Diagnostic.from_node(node, message=cls.message)
            case _:
                return None


# Restrict control flow constructs. ###########################################


class NoStandaloneExpressionRule(BaseRule):
    message = "Expressions may not appear as statements"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not isinstance(node, ast.Expr):
            return None
        match node:
            case ast.Expr(value=value) if any(
                is_function_called(value, name)
                for name in ("observe", "factor")
            ):
                return None
            case _:
                return Diagnostic.from_node(node, message=cls.message)


class RestrictForLoopIteratorRule(BaseRule):
    message = "For-loops may only use `range`"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not isinstance(node, (ast.For, ast.AsyncFor)):
            return None
        match node.iter:
            case ast.Call(func=ast.Name(id="range")):
                return None
            case _:
                return Diagnostic.from_node(node.iter, message=cls.message)


class NoForElseRule(BaseRule):
    message = "For-loops may not have `else` blocks"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.For, ast.AsyncFor)) and node.orelse
            else None
        )


class NoWhileElseRule(BaseRule):
    message = "While-loops may not have `else` blocks"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.While) and node.orelse
            else None
        )


class NoWithStatementRule(BaseRule):
    message = "With statements are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.With, ast.AsyncWith))
            else None
        )


class NoMatchRule(BaseRule):
    message = "The match control-flow construct is prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Match)
            else None
        )


class NoAsynchronousStatementRule(BaseRule):
    message = "Asynchronous statements are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(
                node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith)
            )
            else None
        )


class NoPassRule(BaseRule):
    message = "Pass statements are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Pass)
            else None
        )


class NoEmptyReturnRule(BaseRule):
    message = "Empty returns are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Return) and not node.value
            else None
        )


# Prohibit exception handling. ################################################


class NoRaiseExceptionRule(BaseRule):
    message = "Raising exceptions is prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Raise)
            else None
        )


class NoTryExceptRule(BaseRule):
    message = "The try-except control-flow is prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, (ast.Try, ast.TryStar))
            else None
        )


class NoAssertRule(BaseRule):
    message = "Assertions are prohibited"

    @override
    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Assert)
            else None
        )
