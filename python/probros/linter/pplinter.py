# mypy: disable-error-code="method-assign"
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

        # Represent whether or not this linter has entered a program.
        self._entered: bool = False

        # Fake method overloading for static- and instance-methods.
        self.is_probabilistic_program = self._is_probabilistic_program

        super().__init__(**kwargs)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Prohibit nested functions.

        This allows the first function to pass, because, in this case, it is
        expected to be the probabilistic program's function definition.

        Severity of this diagnostic is `ERROR`.

        Args:
            node: The node to be analyzed.
        """

        if not self._entered:
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

        If this is called from an instantiated linter, a `WARNING` is added to
        the diagnostics of that instance in case of an unindentifiable
        decorator.

        Args:
            node: The node to check.

        Returns:
            True if this could be identified as a probabilistic program, False
            otherwise.
        """

        result, _ = cls.check_and_verify_decorators(node)
        return result

    def _is_probabilistic_program(self, node: ast.FunctionDef) -> bool:
        """Checks whether or not this declares a probabilistic program.

        This adds a `WARNING` to the diagnostics in case a decorator could not
        be identified.

        Note, this method overrides the namesake method (without leading `_`)
        in case of instantiation. Therefore, look at that method's
        documentation for further details.

        Args:
            node: The node to check.

        Returns:
            True if this could be identified as a probabilistic program, False
            otherwise.
        """

        result, diagnostics = self.check_and_verify_decorators(node)
        self.diagnostics + diagnostics
        return result

    @staticmethod
    def check_and_verify_decorators(
        node: ast.FunctionDef,
    ) -> Tuple[bool, list[Diagnostic]]:
        """Checks whether or not this declares a probabilistic program.

        Note that this only checks for the string of the decorator to match
        `_DECORATOR_NAME` currently, no actual testing is done to ensure the
        origin of the decorator. This may lead to incorrect identification of
        functions in case other decorators share that name.

        For clarities sake, this merely verifies if this function's signature
        declares it as a probabilistic program, i.e. has the appropriate
        decorator, this does not do any form or validation or analysis.

        Args:
            node: The node to check.

        Returns:
            `(True, [])` if this could be identified as a probabilistic
            program, `(False, <Diagnostics>)` otherwise. Where `<Diagnostics>`
            may be a non-empty list with `WARNING`s about any unidentifiable
            decorator.
        """

        result = any(
            isinstance(decorator, ast.Attribute)
            and decorator.attr == _DECORATOR_NAME
            or isinstance(decorator, ast.Name)
            and decorator.id == _DECORATOR_NAME
            for decorator in node.decorator_list
        )
        diagnostics = []

        if not result:
            unverified = list(
                filter(
                    lambda decorator: not isinstance(decorator, ast.Attribute)
                    and not isinstance(decorator, ast.Name),
                    node.decorator_list,
                )
            )
            if unverified:
                log.warning(
                    "Could not verify at least one decorator"
                    f" of '{node.name}'…"
                )
            for decorator in unverified:
                log.debug(f"Could not verify decorator: {ast.dump(decorator)}")
                diagnostics.append(
                    Diagnostic.from_node(
                        decorator,
                        "Could not verify decorator.",
                        severity=Severity.WARNING,
                    )
                )

        return (result, diagnostics)
