import ast
import logging
from dataclasses import dataclass
from enum import Enum

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
        logging.debug(f"Initialized linter with {self.diagnostics=}.")

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
        self.visit(node)
        diagnostics = self.diagnostics
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

        if any(
            isinstance(decorator, ast.Attribute)
            and decorator.attr == _DECORATOR_NAME
            or isinstance(decorator, ast.Name)
            and decorator.id == _DECORATOR_NAME
            for decorator in node.decorator_list
        ):
            logging.debug(
                f"Found probabilistic program '{node.name}',"
                " calling specialized linter…"
            )
            pplinter = PPLinter()
            pplinter.visit(node)
            self.diagnostics += map(
                lambda diagnostic: str(diagnostic),
                pplinter.diagnostics,
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

        logging.debug(
            "Initialized probabilistic program linter"
            f" with {self.diagnostics=}."
        )

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Prohibit nested functions.

        This allows the first function to pass, because, in this case, it is
        expected to be the probabilistic program's function definition.

        Severity of this diagnostic is `ERROR`.

        Args:
            node: The node to be analyzed.
        """

        if not self._entered:
            self._entered = True
            self.generic_visit(node)
            self._entered = False
            return

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


def lint_code(code: str) -> list[str] | None:
    """Lint the provided python code.

    Args:
        code: The Python code to be linted.

    Returns:
        The diagnostics found by the linter as strings or `None` in case of
        errors. All diagnostics identified by the linter and any runtime errors
        are logged.
    """

    logging.debug("Running linter on given code " + f"'{code[:25]!a}…'.")
    linter = Linter()
    try:
        tree = ast.parse(code)
    except ValueError:
        logging.warn("Received invalid data.")
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
