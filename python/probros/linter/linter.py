import ast
import logging as log
from typing import Callable, Tuple

from base_linter import BaseLinter, Diagnostic
from pplinter import PPLinter


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
