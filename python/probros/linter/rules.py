import ast
from abc import ABC, abstractmethod

from diagnostic import Diagnostic


class BaseRule(ABC):

    message: str

    @classmethod
    @abstractmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        raise NotImplementedError("Subclasses must implement this.")


class NoNestedFunctionsRule(BaseRule):

    message = "Nested functions are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.FunctionDef)
            or isinstance(node, ast.AsyncFunctionDef)
            else None
        )


class NoNestedClassesRule(BaseRule):

    message = "Nested classes are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.ClassDef)
            else None
        )


class NoDeleteStatementRule(BaseRule):

    message = "Delete statements are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Delete)
            else None
        )


class NoTypeAliasRule(BaseRule):

    message = "Type aliasing is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.TypeAlias)
            else None
        )


class NoAsyncRule(BaseRule):

    message = "Asynchrony is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        match node:
            case (
                ast.AsyncFunctionDef()
                | ast.AsyncFor()  # should be redundant
                | ast.AsyncWith()  # --"--
                | ast.Await()  # --"--
            ):
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


class NoFstringRule(BaseRule):

    message = "F-Strings are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.FormattedValue)
            or isinstance(node, ast.JoinedStr)
            else None
        )


class NoDeconstructorRule(BaseRule):

    message = "Deconstructors are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        # Deconstruction can only occur on `Assign`, `AnnAssign` (annotated
        # assign) and `AugAssign` (augmented assign) cannot use deconstructors.
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Tuple) or isinstance(target, ast.List)
                for target in node.targets
            )
            else None
        )


class NoChainedAssignmentRule(BaseRule):

    message = "Chained assignments are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Assign) and len(node.targets) > 1
            else None
        )


class NoMatchRule(BaseRule):

    message = "The match control-flow construct is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Match)
            else None
        )


class NoRaiseExceptionRule(BaseRule):

    message = "Raising exceptions is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Raise)
            else None
        )


class NoTryExceptRule(BaseRule):

    message = "The try-except control-flow is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Try) or isinstance(node, ast.TryStar)
            else None
        )


class NoAssertRule(BaseRule):

    message = "Assertions are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Assert)
            else None
        )


class NoImportRule(BaseRule):

    message = "Importing is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)
            else None
        )


class NoGlobalOrNonlocalDeclarationRule(BaseRule):

    message = "Declaring global variables is prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Global) or isinstance(node, ast.Nonlocal)
            else None
        )


class NoPassRule(BaseRule):

    message = "Pass statements are prohibited"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        return (
            Diagnostic.from_node(node, message=cls.message)
            if isinstance(node, ast.Pass)
            else None
        )


class RestrictForLoopRule(BaseRule):

    message = "For-loops may only use `range`"

    @classmethod
    def check(cls, node: ast.AST) -> Diagnostic | None:
        if not isinstance(node, ast.For):
            return None
        match node.iter:
            case ast.Call(func=ast.Name(id="range")):
                return None
            case _:
                return Diagnostic.from_node(node.iter, message=cls.message)
