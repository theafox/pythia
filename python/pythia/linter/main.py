"""The main components of the `linter` module.

The `linter` module is designed to provide the ability to lint Python
code conforming to _PyThia_ specifications. This file provides the main
components of this functionality.

Usage:
    For usage in a script see the package documentation (`__init__.py`). For
    usage as a CLI tool see the module documentation (`__main__.py`).

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

import ast
import logging
import sys
from enum import IntEnum
from itertools import chain
from typing import Callable, Iterable, override

from linter import Diagnostic, Severity, rules

# NOTE: extract this dynamically from `probros` to future-proof for changes?
_DECORATOR_NAME = "probabilistic_program"

log = logging.getLogger(__name__)


def _display(item: str | ast.AST, maximum_length: int = 25) -> str:
    r"""Convert the item to a readable representation.

    This is intended to be used for logging. It escapes special characters such
    as `\t` and limits the maximum length of the string. In case an `ast` node
    is given, dump it to make it readable.

    Args:
        item: The item to make readable.
        maximum_length: The maximum length of the resulting string.

    Returns:
        A readable representation of the given item.
    """
    message = item if isinstance(item, str) else ast.dump(item)
    message = message.encode("unicode_escape", "backslashreplace").decode()
    if len(message) > maximum_length:
        message = f"{message[:maximum_length]}…"
    return message


class ExitCode(IntEnum):
    """An enumeration which defines exit codes.

    Attributes:
        INVALID_ARGUMENTS: The user provided invalid arguments.
        READ_ERROR: An error occurred while reading the input.
        PARSE_ERROR: An error occurred while parsing the input.
        LINTING_ERROR: The translation attempt resulted in an error.
    """

    # User generated and input errors.
    INVALID_ARGUMENTS = 10
    READ_ERROR = 11
    PARSE_ERROR = 12
    # Runtime errors.
    LINTING_ERROR = 20


class Linter(ast.NodeVisitor):
    """A general purpose linter to validate python code.

    This linter allows to specify entry-points to code of interest. This
    enables the user to disregard large portions of the code and focus on
    certain aspects of it to lint.

    The current implementation does not enter any further into the syntax tree
    upon analyzing a node which violates rules.

    Note that, the entry-point-node itself is _not_ validated using those
    rules, `analyze_entry_point` may be used for this purpose.

    Analysis on porential entry-points using `analyze_entry_point` checks any
    node outside code of interest. It is therefore independent of the check for
    entry-point nodes and does _not_ guarentee that the passed node is a valid
    entry-point.
    In  case `analyze_entry_point` returns (at least) one diagnostic of the
    error-level, the node is skipped, even as an entry-point, i.e. no further
    diagnosis is done on this node's children.

    Attributes:
        rules: The rules to apply to code of interest.
        is_entry_point: A function to identify entry-points.
        analyze_entry_point: A function to analyze the entry-point itself.
        extensive_diagnosis: Whether to continue searching for diagnostics
            after one was already found.
        diagnostics: The list of currently found diagnostics.
    """

    @override
    def __init__(
        self,
        rules: Iterable[type[rules.BaseRule]],
        is_entry_point: Callable[[ast.AST], bool],
        analyze_entry_point: Callable[
            [ast.AST], Iterable[Diagnostic]
        ] = lambda *args, **kwargs: [],
        extensive_diagnosis: bool = False,
        **kwargs,
    ):
        """Initialize the linter.

        Args:
            rules: The rules to apply to code of interest.
            is_entry_point: A function to identify entry-points.
            analyze_entry_point: A function to analyze the entry-point itself.
            extensive_diagnosis: Whether to continue searching for diagnostics
                after one was already found.
            **kwargs: Any additional key-word-arguments will be handed to the
                super-class initialization.
        """

        super().__init__(**kwargs)

        self.rules = rules
        self.is_entry_point = is_entry_point
        self.analyze_entry_point = analyze_entry_point
        self.extensive_diagnosis = extensive_diagnosis

        self.diagnostics: list[Diagnostic] = []
        self._entered: bool = False
        self._found_outside: bool = False

    @override
    def generic_visit(self, node: ast.AST) -> None:
        """Identify entry-points and apply rules.

        This class is overridden from the parent class. It will be called
        whenever a node is encountered during the walk throug the tree. For
        this reason it is not recommended to subclass this and add any
        `visit_*` methods.

        Args:
            node: The node to identify or analyze.
        """

        # Outside code of interest…
        if not self._entered:
            entry_point_diagnostics = self.analyze_entry_point(node)
            self.diagnostics += entry_point_diagnostics
            if not self.is_entry_point(node):
                if not list(ast.iter_child_nodes(node)):
                    # Found a leaf node outside code-of-interest.
                    self._found_outside = True
                super().generic_visit(node)
            elif not any(
                diagnostic.severity == Severity.ERROR
                for diagnostic in entry_point_diagnostics
            ):
                log.debug("Found admissible node: %s.", _display(node))
                self._entered = True
                super().generic_visit(node)
                self._entered = False
            else:
                log.debug(
                    "Entry-point analysis found an error,"
                    " skipping admissible node: %s.",
                    _display(node),
                )
            return

        # Inside code of interest…
        diagnostics: list[Diagnostic] = [
            diagnostic
            for diagnostic in [rule.check(node) for rule in self.rules]
            if diagnostic
        ]
        if diagnostics:
            log.debug(
                "Rules (%d) were applicable: %s",
                len(diagnostics),
                "; ".join(map(repr, diagnostics)),
            )
            self.diagnostics += diagnostics
        if not diagnostics or self.extensive_diagnosis:
            # Only enter further into nodes which do _not_ violate any rules
            # (or in case extensive diagnosis is requested).
            super().generic_visit(node)

    def lint(self, tree: ast.AST) -> list[Diagnostic]:
        """Lint the provided node.

        Args:
            tree: The node on which to run the linter on.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug("Linting tree: %s.", _display(tree))

        self.diagnostics = []
        self._entered = False
        self._found_outside = False
        self.visit(tree)
        log.debug(
            "Linting finished, got %d diagnostic(s).", len(self.diagnostics)
        )

        diagnostics: list[Diagnostic] = self.diagnostics
        self.diagnostics = []
        return diagnostics

    def lint_code(self, code: str) -> list[Diagnostic]:
        """Lint the provided code.

        Args:
            code: The code on which to run the linter on.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug("Parsing code: %s.", _display(code))
        try:
            tree: ast.AST = ast.parse(code)
        except (SyntaxError, ValueError):
            log.fatal("Could not parse code: %s.", _display(code))
            exit(ExitCode.PARSE_ERROR)
        return self.lint(tree)

    def lint_file(self, path: str) -> list[Diagnostic]:
        """Lint the file located at the provided file-path.

        Args:
            path: The file-path pointing to the file on which to run the
                linter.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug("Reading file: %s.", _display(path))
        try:
            with open(path, "r") as file:
                code: str = file.read()
        except IOError:
            log.fatal("Could not read file: %s.", _display(path))
            exit(ExitCode.READ_ERROR)
        return self.lint_code(code)

    def lint_stdin(self) -> list[Diagnostic]:
        """Lint the input from stdin.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug("Reading from stdin.")
        try:
            code: str = sys.stdin.read()
        except IOError:
            log.fatal("Could not read from stdin.")
            exit(ExitCode.READ_ERROR)
        return self.lint_code(code)

    def found_code_outside(self) -> bool:
        """Whether code was found outside code-of-interest in the last linting.

        Returns:
            In case any leaf-node was found outside code-of-interest returns
            `True`, `False` otherwise.
        """

        return self._found_outside


def _is_probabilistic_program_entry_point(node: ast.AST) -> bool:
    """Checks whether or not this declares a probabilistic program.

    Note that this only checks for the string of the function's decorator to
    match `_DECORATOR_NAME` currently, no actual testing is done to ensure the
    origin of the decorator. This may lead to incorrect identification of
    functions in case other decorators share that name.

    Args:
        node: The node to check.

    Returns:
        True if this could be identified as a probabilistic program, False
        otherwise.
    """

    return isinstance(node, ast.FunctionDef) and any(
        isinstance(decorator, ast.Attribute)
        and decorator.attr == _DECORATOR_NAME
        or isinstance(decorator, ast.Name)
        and decorator.id == _DECORATOR_NAME
        for decorator in node.decorator_list
    )


def _analyze_probabilistic_program_entry_point(
    node: ast.AST,
) -> Iterable[Diagnostic]:
    """Analyze the decorators of potential probabilistic program declarations.

    Only decorators of type `Name` and `Attribute` will be recognized, any
    others receive a diagnostic.

    This additionally checks for any decorators on classes and asynchronous
    functions to warn users that their usage is intended for functions only.

    Args:
        node: The function node to analyze.

    Returns:
        A list of diagnostics for all unrecognized decorators.
    """

    if (
        isinstance(node, ast.ClassDef)
        or isinstance(node, ast.AsyncFunctionDef)
    ) and any(
        isinstance(decorator, ast.Attribute)
        and decorator.attr == _DECORATOR_NAME
        or isinstance(decorator, ast.Name)
        and decorator.id == _DECORATOR_NAME
        for decorator in node.decorator_list
    ):
        return [
            Diagnostic.from_node(
                node,
                message="Probabilistic program decorators are intended for"
                " functions only",
                severity=Severity.INFORMATION,
            )
        ]
    elif not isinstance(node, ast.FunctionDef):
        return []

    diagnostics: list[Diagnostic] = []

    # In case some decorators could not be verified…
    unrecognized: list[ast.expr] = list(
        filter(
            lambda decorator: not isinstance(
                decorator,
                (ast.Attribute, ast.Name, ast.Call),
            ),
            node.decorator_list,
        )
    )
    if unrecognized:
        log.warning(
            "Could not verify at least one decorator of `%s`.", node.name
        )
    for decorator in unrecognized:
        log.debug("Could not verify decorator: %s.", ast.dump(decorator))
        diagnostics.append(
            Diagnostic.from_node(
                decorator,
                "Could not verify decorator.",
                severity=Severity.WARNING,
            )
        )

    # In case the entry-point is valid…
    if isinstance(node, ast.FunctionDef) and any(
        isinstance(decorator, ast.Attribute)
        and decorator.attr == _DECORATOR_NAME
        or isinstance(decorator, ast.Name)
        and decorator.id == _DECORATOR_NAME
        for decorator in node.decorator_list
    ):
        # warn about discouraged argument-types.
        if (
            node.args.kwonlyargs
            or node.args.vararg  # `*args`
            or node.args.kwarg  # `**kwargs`
            or node.args.kw_defaults  # `arg=3` as a keyword argument
            or node.args.defaults  # `arg=3` as a positional argument
        ):
            diagnostics.append(
                Diagnostic.from_node(
                    node,
                    message="The use of keyword arguments, `*args`"
                    ", `**kwargs`, and defaults is discouraged",
                    severity=Severity.ERROR,
                )
            )

        # inform about discouraged typing.
        if any(
            argument.annotation
            for argument in chain(
                node.args.args,
                node.args.posonlyargs,
                (node.args.vararg,),
                (node.args.kwarg,),
            )
            if argument
        ):
            diagnostics.append(
                Diagnostic.from_node(
                    node,
                    message="Typing is disouraged",
                    severity=Severity.WARNING,
                )
            )

    return diagnostics


def default_probabilistic_program_linter() -> Linter:
    """Construct the default linter for probabilistic programs.

    This includes all rules to conform to the specifications of a probabilistic
    program.

    Returns:
        A linter which may be run on any python code to validate any
        probabilistic programs.
    """
    return Linter(
        {
            # Statement rules.
            rules.NoNestedFunctionsRule,
            rules.NoNestedClassesRule,
            rules.NoImportRule,
            rules.NoGlobalOrNonlocalDeclarationRule,
            rules.NoDeleteStatementRule,
            rules.NoTypeAliasRule,
            rules.NoDeconstructorRule,
            rules.NoChainedAssignmentRule,
            rules.NoAugmentedAssignRule,
            rules.WarnAnnotatedAssignRule,
            rules.NoAttributeAssignRule,
            rules.NoStandaloneExpressionRule,
            rules.RestrictForLoopIteratorRule,
            rules.NoForElseRule,
            rules.NoWhileElseRule,
            rules.NoWithStatementRule,
            rules.NoMatchRule,
            rules.NoAsynchronousStatementRule,
            rules.NoPassRule,
            rules.NoEmptyReturnRule,
            rules.NoRaiseExceptionRule,
            rules.NoTryExceptRule,
            rules.NoAssertRule,
            # Expression rules.
            rules.RestrictBinaryOperatorsRule,
            rules.RestrictComparisonOperatorsRule,
            rules.RestrictUnaryOperatorsRule,
            rules.NoWalrusOperatorRule,
            rules.NoLambdaRule,
            rules.NoInlineIfRule,
            rules.NoDictionaryRule,
            rules.NoSetRule,
            rules.NoComprehensionAndGeneratorRule,
            rules.NoAsynchronousExpressionRule,
            rules.NoYieldRule,
            rules.NoFstringRule,
            rules.NoStarredRule,
            rules.NoTypeParameterRule,
            rules.NoSliceRule,
            rules.NoMultipleSubscriptRule,
            # Probabilistic-programming-specific rules.
            rules.RestrictSampleCallStructureRule,
            rules.RestrictObserveCallStructureRule,
            rules.RestrictFactorCallStructureRule,
            rules.RestrictIndexedAddressCallStructureRule,
            rules.RestrictVectorConstructorCallStructureRule,
            rules.RestrictArrayConstructorCallStructureRule,
        },
        _is_probabilistic_program_entry_point,
        _analyze_probabilistic_program_entry_point,
    )
