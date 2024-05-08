"""A linter for probabilistic programs.

TODO: add specifications!

Example:
    This script may also be used as a CLI tool to lint files according to those
    rules. When used as a CLI tool, a `-v`/`--verbose` flag may be provided for
    extensive logging messages. And one positional argument must be provided
    which either points to a file or, if the path is not valid or the file
    could not be opened, the argument is interpreted as code instead.

        $ python3 linter.py -v test.py
        * Received 'test.py'… as a string, try interpreting it as a file-path.
        * Identified 'test.py'… as a file, reading the contents.
        * Parsing 'import probros\n\n\n# This s'… as code.
        …

        $ python3 linter.py test.py
        Linter ran successfully, received 3 hints.
          51:4: ERROR: Nested functions are not allowed
          …

Attributes:
    Linter: This class represents the linter for probabilistic programs used
        by `lint` and `main`. This class inherits from `ast.NodeVisitor` and
        has a `run` function for convenient usage.
    lint: A function which represents the linting functionality. The argument,
        similar to the CLI functionality, first tries interpreting this as a
        file-path, if unsuccessful, the argument is parsed as code instead.
    main: This function includes the setup for the CLI functionality.

Meta-Information:
    Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
    Version: 0.1.0
"""

import ast
import logging as log
from typing import Callable

from base_linter import BaseLinter, Diagnostic
from pplinter import PPLinter


class Linter(BaseLinter):
    """A linter to validate any probabilistic programs found.

    Attributes:
        specialized_linter: The linter to use for identified probabilistic
            programs.
        is_probabilistic_program: A function which checks whether or not a
            function node could be identified as a probabilistic program.
        analyze_decorator: A function which analyzes if any decorators of a
            function node could not be recognized.
    """

    def __init__(
        self,
        probabilistic_program_linter: BaseLinter,
        is_probabilistic_program: Callable[[ast.FunctionDef], bool],
        analyze_decorator: Callable[
            [ast.FunctionDef], list[Diagnostic]
        ] = lambda *args, **kwargs: [],
        **kwargs,
    ) -> None:
        """Initialize the linter.

        Args:
            probabilistic_program_linter: Linter to analyze individual
                probabilistic programs.
            is_probabilistic_program: A function which checks whether or not a
                function node could be identified as a probabilistic program.
            analyze_decorator: A function which analyzes if any decorators of a
                function node could not be recognized.
            **kwargs: Any further arguments, those will be handed to the
                initialization method of any super classes.
        """

        super().__init__(**kwargs)
        self.specialized_linter = probabilistic_program_linter
        self.is_admissible = is_probabilistic_program
        self.analyze_decorator = analyze_decorator

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Hand off analyzing probabilistic programs, ignore anything else.

        Args:
            node: The function node to be analyzed.
        """

        diagnostics = self.analyze_decorator(node)
        if self.is_admissible(node):
            log.debug(
                f"Found probabilistic program '{node.name}',"
                " calling specialized linter."
            )
            diagnostics += self.specialized_linter.run(node)
        else:
            log.debug(f"Skipping function '{node.name}'")

        log.debug(f"Collecting {len(diagnostics)} diagnostic(s).")
        self.diagnostics += diagnostics


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

    linter = Linter(
        PPLinter(),
        PPLinter.is_probabilistic_program,
        PPLinter.analyze_decorators,
    )
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
        # Prepend debugging messages with `* ` to differentiate them from
        # normal outputs.

        standard = log.StreamHandler(sys.stdout)
        standard.addFilter(lambda record: record.levelno != log.DEBUG)

        verbose = log.StreamHandler(sys.stdout)
        verbose.addFilter(lambda record: record.levelno == log.DEBUG)
        verbose.setFormatter(log.Formatter("* %(message)s"))

        log.basicConfig(
            format="%(message)s",
            level=log.DEBUG,
            handlers=(standard, verbose),
        )
    else:
        log.basicConfig(format="%(message)s", level=log.INFO)

    diagnostics = lint(args.target)
    hints = list(map(lambda diagnostic: str(diagnostic), diagnostics))

    log.info(f"Linter ran successfully, received {len(hints)} hints.")
    for hint in hints:
        log.info(str(hint))


if __name__ == "__main__":
    main()
