# mypy: disable-error-code="method-assign"
import ast
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Self, Tuple

# TODO: extract this dynamically from `probros` to future-proof for changes?
_DECORATOR_NAME = "probabilistic_program"


class Severity(Enum):
    """This represents the severity of diagnostics.

    Attributes:
        WARNING: Indicates a warning-level severity.
        ERROR: Indicates a warning-level severity.
    """

    WARNING = 10
    ERROR = 20

    def __str__(self) -> str:
        """Get the string representation of the severity.

        Returns:
            The string representation of the severity.
        """

        return str(self.name)


@dataclass(frozen=True, kw_only=True)
class Diagnostic:
    """A representation of diagnostics.

    Attributes:
        line: The line number of the diagnostic.
        end_line: The ending line number of the diagnostic.
        column: The column number of the diagnostic.
        end_column: The ending column number of the diagnostic.
        message: The message of the diagnostic.
        severity: The severity of the diagnostic.
    """

    line: int
    end_line: int
    column: int
    end_column: int
    message: str
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        """Get a presentable representation of this diangostic.

        Returns:
            A one-line message including the line number, column number,
            severity, and message.
        """
        return (
            f"{self.line:4d}:{self.column}:\t{self.severity}: {self.message}"
        )

    @classmethod
    def from_node(
        cls,
        node: ast.AST,
        message: str,
        severity: Severity = Severity.ERROR,
    ) -> Self:
        return cls(
            line=node.lineno,
            end_line=(
                node.end_lineno
                if node.end_lineno and node.end_lineno >= node.lineno
                else node.lineno
            ),
            column=node.col_offset,
            end_column=(
                node.end_col_offset
                if node.end_col_offset
                and node.end_col_offset >= node.col_offset
                else node.col_offset
            ),
            message=message,
            severity=severity,
        )


class Linter(ast.NodeVisitor):
    """A linter to validate any probabilistic programs found within the code.

    This linter focuses on programs implementing probabilistic programs
    according to the specifications in `docs.ipynb`. Therefore, only functions
    annotated as such are checked, any other part of the code is ignored.

    Attributes:
        diagnostics: A list to store found diagnostics
    """

    def __init__(self) -> None:
        """Initialize the linter."""
        self.diagnostics: list[str] = []

    def run(self, node: ast.AST) -> list[str]:
        """Run the linter and receive any diagnostics.

        This method is merely a wrapper to empty any previous diagnostics, call
        `visit` and empty the diagnostics again afterwards.

        Args:
            node: The node on which to run the linter on.

        Returns:
            A list of any diagnostics found, formatted into a string.
        """

        self.diagnostics = []

        logging.debug(f"Running linter on node '{ast.dump(node)[:25]}…'.")
        self.visit(node)
        diagnostics = self.diagnostics
        logging.debug(f"Linter finished, got {len(diagnostics)} diagnostics.")

        self.diagnostics = []
        return diagnostics

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Hand off analyzing probabilistic programs, ignore anything else.

        Note that this only checks for the string of the decorator to match
        `_DECORATOR_NAME` currently, no actual testing is done to ensure the
        origin of the decorator. This may lead to incorrect identification of
        functions in case other decorators share that name.

        Args:
            node: The node to be analyzed.
        """

        is_program, diagnostics = PPLinter.check_and_verify_decorators(node)
        if is_program:
            logging.debug(
                f"Found probabilistic program '{node.name}',"
                " calling specialized linter."
            )
            pplinter = PPLinter()
            pplinter.visit(node)
            diagnostics += pplinter.diagnostics
        else:
            logging.debug(f"Skipping function '{node.name}'")

        logging.debug(
            f"Converting and congregating {len(diagnostics)} diagnostic(s)."
        )
        self.diagnostics += map(
            lambda diagnostic: str(diagnostic),
            diagnostics,
        )


class PPLinter(ast.NodeVisitor):
    """A linter to validate individual probabilistic programs.

    This linter is geared to analyze individual probabilistic programs
    according to the definition in `docs.ipynb`. Thus, this linter is not
    designed to be used as a standalone linter.

    Attributes:
        diagnostics: A list to store found diagnostics.
    """

    def __init__(self) -> None:
        """Initialize the linter."""

        self.diagnostics: list[Diagnostic] = []

        # Represent whether or not this linter has entered a program.
        self._entered: bool = False

        # Fake method overloading for static- and instance-methods.
        self.is_probabilistic_program = self._is_probabilistic_program

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
                logging.debug("Entered probabilistic program analysis.")
                self._entered = True
                self.generic_visit(node)
                self._entered = False
            else:
                logging.warning(
                    "Encountered non-probabilistic program function"
                    " on first entry."
                )
            return

        logging.debug("Found invalidly nested function.")
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
                logging.warning(
                    "Could not verify at least one decorator"
                    f" of '{node.name}'…"
                )
            for decorator in unverified:
                logging.debug(
                    f"Could not verify decorator: {ast.dump(decorator)}"
                )
                diagnostics.append(
                    Diagnostic.from_node(
                        decorator,
                        "Could not verify decorator.",
                        severity=Severity.WARNING,
                    )
                )

        return (result, diagnostics)


def lint_code(code: str) -> list[str] | None:
    """Lint the provided python code.

    Args:
        code: The Python code to be linted.

    Returns:
        The diagnostics found by the linter as strings or `None` in case of
        errors. All diagnostics identified by the linter and any runtime errors
        are logged.
    """

    logging.debug(f"Running linter on given code {code[:25]!a}….")
    linter = Linter()
    try:
        tree = ast.parse(code)
    except ValueError:
        logging.warning("Received invalid data.")
        return None

    diagnostics = linter.run(tree)

    logging.info(
        f"Linter ran successfully, found {len(diagnostics)} diagnostics."
    )
    for diagnostic in diagnostics:
        logging.info(diagnostic)

    return diagnostics


def lint_file(filepath: str) -> list[str] | None:
    """Lint the provided file.

    This currently reads the whole file into memory and parses it afterwards.
    Therefore, this may cause problems with very large files.

    Args:
        code: The path to the file containing the Python code to be linted.

    Returns:
        The diagnostics found by the linter as strings or `None` in case of
        errors. All diagnostics identified by the linter and any runtime errors
        are logged.
    """

    logging.debug(f"Reading file '{filepath}'.")
    try:
        with open(filepath, "r") as file:
            code = file.read()
    except IOError as error:
        logging.fatal(f"Failed to open file '{filepath}': {error}")
        return None

    return lint_code(code)


def main() -> None:
    """Parse CLI arguments and execute the linter.

    This uses `argparse` to decypher any arguments. Valid arguments are:
    - `-v` / `--verbose` to print debugging messages, and
    - either a filepath as a positional argument, or
    - `-c` / `--code` with the code to analyze.
      The filepath and `-c`/`--code` are mutually exclusive but one is
      required.
    """

    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose messages",
    )
    code_origin = parser.add_mutually_exclusive_group(required=True)
    code_origin.add_argument(
        "filepath", help="File to run the linter on", type=str, nargs="?"
    )
    code_origin.add_argument("-c", "--code", help="The code to lint", type=str)
    args = parser.parse_args()

    if args.verbose:
        # Use two different handlers to print the standard / debugging
        # information. This also allows redirecting the output if required.
        # Preprend debugging messages with `* ` to differentiate them from
        # normal outputs.

        standard = logging.StreamHandler(sys.stdout)
        standard.addFilter(lambda record: record.levelno != logging.DEBUG)

        verbose = logging.StreamHandler(sys.stdout)
        verbose.addFilter(lambda record: record.levelno == logging.DEBUG)
        verbose.setFormatter(logging.Formatter("* %(message)s"))

        logging.basicConfig(
            format="%(message)s",
            level=logging.DEBUG,
            handlers=(standard, verbose),
        )
    else:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

    if args.filepath and not args.code:
        lint_file(args.filepath)
    elif args.code and not args.filepath:
        lint_code(args.code)
    else:
        raise RuntimeError("Reached unreachable code.")


if __name__ == "__main__":
    main()
