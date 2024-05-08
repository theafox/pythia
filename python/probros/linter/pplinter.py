import ast
import logging as log
from typing import Tuple

from base_linter import BaseLinter, Diagnostic, Severity

# TODO: extract this dynamically from `probros` to future-proof for changes?
_DECORATOR_NAME = "probabilistic_program"


class PPLinter(BaseLinter):
    """A linter to validate individual probabilistic programs.

    This linter is geared to analyze individual probabilistic programs.
    Thus, this linter is not designed to be used as a standalone linter.
    """

    def __init__(self, **kwargs) -> None:
        """Initialize the linter.

        Args:
            **kwargs: Any further arguments, those will be handed to the
                initialization method of any super classes.
        """

        super().__init__(**kwargs)

        # Represent whether or not this linter has entered a program.
        self._entered: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Prohibit nested functions.

        This allows the first function to pass, because, in this case, it is
        expected to be the probabilistic program's function definition.

        Severity of this diagnostic is `ERROR`.

        Args:
            node: The node to be analyzed.
        """

        if not self._entered:
            self.diagnostics += self.analyze_decorators(node)
            if self.is_probabilistic_program(node):
                log.debug("Entered probabilistic program analysis.")
                self._entered = True
                self.generic_visit(node)
                self._entered = False
            else:
                log.warning(
                    "Encountered non-probabilistic program function"
                    " on first entry."
                )
            return

        log.debug("Found invalidly nested function.")
        self.diagnostics.append(
            Diagnostic(
                line=node.lineno,
                end_line=node.end_lineno if node.end_lineno else node.lineno,
                column=node.col_offset,
                end_column=(
                    node.end_col_offset
                    if node.end_col_offset
                    else node.col_offset
                ),
                message="Nested functions are not allowed",
            )
        )

    @classmethod
    def is_probabilistic_program(cls, node: ast.FunctionDef) -> bool:
        """Checks whether or not this declares a probabilistic program.

        Note that this only checks for the string of the decorator to match
        `_DECORATOR_NAME` currently, no actual testing is done to ensure the
        origin of the decorator. This may lead to incorrect identification of
        functions in case other decorators share that name.

        For clarities sake, this merely verifies if this function's signature
        declares it as a probabilistic program, i.e. has the appropriate
        decorator, this does not do any form or validation or analysis.

        Args:
            node: The function node to check.

        Returns:
            True if this could be identified as a probabilistic program, False
            otherwise.
        """

        is_probabilistic_program, _ = cls._check_analyze_decorators(node)
        return is_probabilistic_program

    @classmethod
    def analyze_decorators(cls, node: ast.FunctionDef) -> list[Diagnostic]:
        """Analyze the decorators of a function.

        Only decorators of type `Name` and `Attribute` will be recognized, any
        others receive a diagnostic.

        Args:
            node: The function node to analyze.

        Returns:
            A list of diagnostics for all unrecognized decorators.
        """

        _, diagnostics = cls._check_analyze_decorators(node)
        return diagnostics

    @staticmethod
    def _check_analyze_decorators(
        node: ast.FunctionDef,
    ) -> Tuple[bool, list[Diagnostic]]:
        """Check whether `node` is a probabilistic program and has unrecognized
        decorators.

        Note that this only checks for the string of the decorator to match
        `_DECORATOR_NAME` currently, no actual testing is done to ensure the
        origin of the decorator. This may lead to incorrect identification of
        functions in case other decorators share that name.

        Only decorators of type `Name` and `Attribute` will be recognized, any
        others receive a diagnostic.

        Both functionalities are consolidated into this "private" function,
        because both require consistent definition of what decorators can be
        recognized.

        Args:
            node: The function node to check and analyze.

        Returns:
            A tuple, whose first element indicates whether or not the function
            could be identified as a probabilistic program. The second element
            may contain any `WARNING`s about unidentifiable decorators.
        """

        # check…
        is_probabilistic_program: bool = any(
            isinstance(decorator, ast.Attribute)
            and decorator.attr == _DECORATOR_NAME
            or isinstance(decorator, ast.Name)
            and decorator.id == _DECORATOR_NAME
            for decorator in node.decorator_list
        )

        # analyze…
        unrecognized: list[ast.expr] = list(
            filter(
                lambda decorator: not isinstance(decorator, ast.Attribute)
                and not isinstance(decorator, ast.Name),
                node.decorator_list,
            )
        )

        if unrecognized:
            log.warning(
                f"Could not verify at least one decorator of '{node.name}'…"
            )

        diagnostics: list[Diagnostic] = []
        for decorator in unrecognized:
            log.debug(f"Could not verify decorator: {ast.dump(decorator)}")
            diagnostics.append(
                Diagnostic.from_node(
                    decorator,
                    "Could not verify decorator.",
                    severity=Severity.WARNING,
                )
            )

        return (is_probabilistic_program, diagnostics)
