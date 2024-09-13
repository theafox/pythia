r"""This script serves as an entry-point for the `linter` package.

This provides a linter for validating code conforming to the PyThia
Meta-Probabilistic-Programming-Language syntax.

Usage:
    ```py
    python -m linter [OPTIONS] <FILE>
    ```

Arguments:
    FILE     File to lint. This option may be replaced with options specifying
             alternative input methodologies.

Options:
    -h, --help                  Show a help message and exit.
    -v, --verbose               Enable verbose debugging information.
    -q, --quiet                 Reduce output to fatal errors or the results.
    -e, --extensive-diagnosis   Continue, even if diagnostics were found.
    --stdin                     Read from standard input instead of SOURCE.
    -c, --code CODE             Code to translate.
    --json                      Output the results in JSON format.

Examples:
    ```sh
    $ python -m linter -e -json model.py
    Linter ran successfully, got 8 diagnostic(s).
    {"diagnostics": [{"line": 13, "end_line": 13, "column": 1, "e…
    ```

    ```sh
    $ python -m linter -v model.py
    * Reading file 'model.py'….
    * Parsing code 'import sys\n\ndef model(data'….
    …
    ```

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

import argparse
import logging
import sys
from dataclasses import asdict
from enum import Enum, IntEnum
from json import dumps
from typing import Sequence, TypedDict

from linter.main import ExitCode, default_probabilistic_program_linter

LINTER = default_probabilistic_program_linter()

log = logging.getLogger(__name__)


class Verbosity(IntEnum):
    """Enumeration of verbosity levels."""

    QUIET = 1
    NORMAL = 5
    VERBOSE = 10


class _Arguments(TypedDict):
    file: str
    verbose: bool
    quiet: bool
    extensive_diagnosis: bool
    stdin: bool
    code: str
    json: bool


def _parse_arguments(arguments: Sequence[str] | None = None) -> _Arguments:
    """Parse the (command-line) arguments.

    This implements the arguments and options according to the specifications
    in the package documentation.

    This uses `argparse` to parse the arguments, therefore, any peculiarities
    related to that package apply here as well. For instance, in case the
    arguments are invalid, this exits.

    Args:
        arguments: The arguments to parse, in case this is `None`, read the
            arguments from the command-line.

    Returns:
        A dictionary containing the parsed results of the input.
    """
    parser = argparse.ArgumentParser(
        description="Lint probabilistic programms conforming to"
        " the _PyThia_ syntax."
    )

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="output more verbose messages",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="only output fatal errors and the results",
    )

    parser.add_argument(
        "-e",
        "--extensive-diagnosis",
        action="store_true",
        help="continue linting, regardless if any diagnostics were found for"
        " that (part of the) code",
        dest="extensive_diagnosis",
    )

    code_origin = parser.add_mutually_exclusive_group(required=True)
    code_origin.add_argument(
        "file", nargs="?", help="file to run the linter on"
    )
    code_origin.add_argument(
        "--stdin", action="store_true", help="read the code from stdin"
    )
    code_origin.add_argument("-c", "--code", help="the code to lint")

    parser.add_argument(
        "--json", action="store_true", help="output the results in JSON format"
    )

    parsed = parser.parse_args(arguments)
    return {
        "file": parsed.file,
        "verbose": parsed.verbose,
        "quiet": parsed.quiet,
        "extensive_diagnosis": parsed.extensive_diagnosis,
        "stdin": parsed.stdin,
        "code": parsed.code,
        "json": parsed.json,
    }


def configure_logger(verbosity: Verbosity) -> None:
    """Configure the logger.

    Use multiple handlers, to allow redirecting the output if required and
    prepending messages with indicators of logging or warning messages. Prepend
    debugging messages with ` * ` and errors with ` ! `.

    Args:
        verbosity: The verbosity of the logger.
    """
    warning = logging.StreamHandler(sys.stdout)
    warning.addFilter(lambda record: logging.ERROR <= record.levelno)
    warning.setFormatter(logging.Formatter(" ! %(message)s"))

    standard = logging.StreamHandler(sys.stdout)
    standard.addFilter(
        lambda record: logging.DEBUG < record.levelno < logging.ERROR
    )
    standard.setFormatter(logging.Formatter("%(message)s"))

    verbose = logging.StreamHandler(sys.stdout)
    verbose.addFilter(lambda record: record.levelno <= logging.DEBUG)
    verbose.setFormatter(logging.Formatter(" * %(message)s"))

    match verbosity:
        case Verbosity.QUIET:
            level = logging.FATAL
            handlers = (warning,)
        case Verbosity.NORMAL:
            level = logging.INFO
            handlers = (warning, standard)
        case Verbosity.VERBOSE:
            level = logging.DEBUG
            handlers = (warning, standard, verbose)

    logging.basicConfig(level=level, handlers=handlers)


def main(arguments: Sequence[str] | None = None) -> None:
    """Parse CLI arguments and execute a linter.

    This exits the program using `sys.exit` in case of any error, invalid
    input, etc. It is therefore not recommended to use this
    function for anything but direct execution of this linter.

    This processes and lints the input in the following steps:

    1. Parse the command-line arguments.
    2. Configure the logger for this package.
    3. Lint the provided input using the _PyThia_ linter.
    4. Output the results according to the instructions.
    """
    parsed = _parse_arguments(arguments)

    configure_logger(
        Verbosity.QUIET
        if parsed["quiet"]
        else Verbosity.VERBOSE
        if parsed["verbose"]
        else Verbosity.NORMAL
    )

    linter = LINTER
    linter.extensive_diagnosis = parsed["extensive_diagnosis"]
    if source := parsed["file"]:
        diagnostics = linter.lint_file(source)
    elif parsed["stdin"]:
        diagnostics = linter.lint_stdin()
    elif source := parsed["code"]:
        diagnostics = linter.lint_code(source)
    else:
        log.fatal("Did not receive any code or code-source")
        sys.exit(ExitCode.INVALID_ARGUMENTS)

    log.info(
        "Linter ran successfully, got %s diagnostic(s).", len(diagnostics)
    )
    if not parsed["quiet"]:
        print()  # buffer between logging and results.
    print(
        "\n".join(map(str, diagnostics))  # print as one block.
        if not parsed["json"]
        else dumps(
            {
                "diagnostics": [
                    asdict(
                        diagnostic,
                        dict_factory=lambda data: {
                            key: value.name
                            if isinstance(value, Enum)
                            else value
                            for key, value in data
                        },
                    )
                    for diagnostic in diagnostics
                ]
            },
            default=str,
        )
    )


if __name__ == "__main__":
    main()
