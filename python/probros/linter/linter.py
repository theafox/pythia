# mypy: disable-error-code="method-assign"
import abc
import ast
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Self, Tuple

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


class BaseLinter(abc.ABC, ast.NodeVisitor):
    """A base class for linters to validate some code.

    Attributes:
        diagnostics: A list to store diagnostics.
    """

    @abc.abstractmethod
    def __init__(self, **kwargs) -> None:
        """Abstract initialization method.

        Args:
            **kwargs: Any further arguments, those will be handed to the
                initialization method of any super classes.
        """

        self.diagnostics: list[Diagnostic] = []
        super().__init__(**kwargs)

    def run(self, target: ast.AST | str) -> list[Diagnostic]:
        """Run the linter and receive any diagnostics.

        In case `node` is given as a string, (i) attempt to interpret it as a
        file-path to read and lint the file, if this fails, (ii) try to lint
        the string itself.

        Args:
            target: The file or code on which to run the linter on.

        Returns:
            A list of any diagnostics found.
        """

        if isinstance(target, str):
            # (i) attempt to interpret `target` as a file-path…
            logging.debug(
                f"Received {target[:25]!a}… as a string,"
                " try interpreting it as a file-path."
            )
            if os.path.isfile(target):
                logging.debug(
                    f"Identified {target[:25]!a}… as a file,"
                    " reading the contents."
                )
                try:
                    with open(target, "r") as file:
                        target = file.read()
                except IOError as error:
                    logging.debug(
                        f"Failed to read {target[:25]!a}… as a file: {error}"
                    )

            # (ii) attempt to parse `target` as code…
            logging.debug(f"Parsing {target[:25]!a}… as code.")
            try:
                target = ast.parse(target)
            except ValueError as error:
                logging.fatal(
                    f"Failed to parse {str(target)[:25]!a}… as code,"
                    f" aborting {self.__class__.__name__}: {error}"
                )
                return []

        logging.debug(
            f"Running {self.__class__.__name__} on"
            f" node {ast.dump(target)[:25]}…."
        )

        self.diagnostics = []
        self.visit(target)

        logging.debug(
            f"{self.__class__.__name__} finished,"
            f" got {len(self.diagnostics)} diagnostics."
        )

        diagnostics = self.diagnostics
        self.diagnostics = []
        return diagnostics


class Linter(BaseLinter):
    """A linter to validate any probabilistic programs found.

    Attributes:
        decorator_verifier: A function to verify if a given node satisfies the
            conditions to count as a "probabilistic program".
        specialized_linter: The linter to use for identified probabilistic
            programs.
    """

    def __init__(
        self,
        decorator_verifier: Callable[
            [ast.FunctionDef],
            Tuple[bool, list[Diagnostic]],
        ],
        probabilistic_program_linter: BaseLinter,
        **kwargs,
    ) -> None:
        """Initialize the linter.

        Args:
            decorator_verifier: Function to verify if a given function node
                constitutes as a "probabilistic program".
            probabilistic_program_linter: Linter to analyze individual
                probabilistic programs.
            **kwargs: Any further arguments, those will be handed to the
                initialization method of any super classes.
        """

        self.decorator_verifier = decorator_verifier
        self.specialized_linter = probabilistic_program_linter
        super().__init__(**kwargs)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Hand off analyzing probabilistic programs, ignore anything else.

        Args:
            node: The function node to be analyzed.
        """

        is_program, diagnostics = self.decorator_verifier(node)
        if is_program:
            logging.debug(
                f"Found probabilistic program '{node.name}',"
                " calling specialized linter."
            )
            diagnostics += self.specialized_linter.run(node)
        else:
            logging.debug(f"Skipping function '{node.name}'")

        logging.debug(f"Collecting {len(diagnostics)} diagnostic(s).")
        self.diagnostics += diagnostics


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


def lint(target: str) -> list[Diagnostic]:
    """Lint the provided file or python code.

    This function (i) attempts to interpret `target` as a file-path to read and
    lint the according file, if this fails, it tries to (ii) lint the string
    itself.

    This currently reads the whole file into memory and parses it afterwards.
    Therefore, this may cause problems with very large files.

    Args:
        target: The file-path or code to be linted.

    Returns:
        The diagnostics found by the linter. All diagnostics identified by the
        linter and any runtime errors are logged.
    """

    linter = Linter(PPLinter.check_and_verify_decorators, PPLinter())
    diagnostics = linter.run(target)
    return diagnostics


def main() -> None:
    """Parse CLI arguments and execute the linter.

    This uses `argparse` to decypher any arguments. Valid arguments are:
    - `-v` / `--verbose` to print debugging messages, and
    - either a filepath or code as a positional argument.

    The positional argument is (i) interpreted as a file-path, if this fails,
    (ii) the argument itself is parsed and linted.
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
    parser.add_argument(
        "target",
        help="File or code to run the linter on",
        type=str,
    )
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

    diagnostics = lint(args.target)
    hints = list(map(lambda diagnostic: str(diagnostic), diagnostics))

    logging.info(f"Linter ran successfully, received {len(hints)} hints.")
    for hint in hints:
        logging.info(str(hint))


if __name__ == "__main__":
    main()
