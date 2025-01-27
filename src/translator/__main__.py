r"""This script serves as an entry-point for the `translator` package.

This provides a translator for mapping code conforming to the PyThia
Meta-Probabilistic-Programming-Language syntax into different languages and/or
frameworks.

Any given input is first validated against the syntax of PyThia before
attempting translation using the PyThia linter. In case any error-level (or
higher) is found, no translation is attempted.

Usage:
    ```py
    python -m translator [OPTIONS] <TARGET> <FILE>
    ```

Arguments:
    TARGET     The target language or framework to translate to.

    FILE       File to translate. This option may be replaced with options
               specifying alternative input methodologies.

Options:
    -h, --help                  Show a help message and exit.
    -v, --verbose               Enable verbose debugging information.
    -q, --quiet                 Reduce output to fatal errors or the results.
    -f, --force                 Skip code validation before translation.
    --stdin                     Read from standard input instead of SOURCE.
    -c, --code CODE             Code to translate.
    -o, --output FILE           Write the results to FILE.
    --output-overwrite FILE     Overwrite FILE with the results.
    --output-append FILE        Append the results to FILE.

Examples:
    ```sh
    $ python -m translator -f -o output.jl Gen model.py
    Translator ran successfully, 92 character(s) and 7 line(s) translated.
    Translation successfully written to file: output.jl.
    ```

    ```sh
    $ python -m translator -v Pyro model.py
    * Reading file: model.py.
    * Parsing code: import sys\n\ndef model(data….
    …
    ```

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

import argparse
import logging
import sys
from collections.abc import Sequence
from enum import IntEnum
from pathlib import Path
from typing import TypedDict

from linter import Severity, default_probabilistic_program_linter
from translator.main import (
    ExitCode,
    default_gen_translator,
    default_pyro_translator,
    default_turing_translator,
)

TRANSLATORS = {
    "pyro": default_pyro_translator(),
    "gen": default_gen_translator(),
    "turing": default_turing_translator(),
}

log = logging.getLogger(__name__)


class Verbosity(IntEnum):
    """Enumeration of verbosity levels."""

    QUIET = 1
    NORMAL = 5
    VERBOSE = 10


class _Arguments(TypedDict):
    target: str
    file: str
    verbose: bool
    quiet: bool
    force: bool
    stdin: bool
    code: str
    output: str
    output_overwrite: str
    output_append: str


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
        description="Translate probabilistic programms from PyThia into "
        + ", ".join(TRANSLATORS.keys())[::-1].replace(",", "ro ,", 1)[::-1]
        + "."
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
        "-f",
        "--force",
        action="store_true",
        help="force translation, regardless of any prior code-validation",
    )
    parser.add_argument(
        "target",
        choices=TRANSLATORS.keys(),
        type=str.lower,
        help="language/framework to translate the code to",
    )

    code_origin = parser.add_mutually_exclusive_group(required=True)
    code_origin.add_argument(
        "file", nargs="?", help="file to run the translator on"
    )
    code_origin.add_argument(
        "--stdin", action="store_true", help="read the code from stdin"
    )
    code_origin.add_argument("-c", "--code", help="the code to lint")

    code_destination = parser.add_mutually_exclusive_group()
    code_destination.add_argument(
        "-o",
        "--output",
        help="file to write the output to (error if it already exists)",
    )
    code_destination.add_argument(
        "--output-overwrite",
        help="file to write the output to (overwriting if it already exists)",
        dest="output_overwrite",
    )
    code_destination.add_argument(
        "--output-append",
        help="file to write the output to (appending if it already exists)",
        dest="output_append",
    )

    parsed = parser.parse_args(arguments)
    return {
        "target": parsed.target,
        "file": parsed.file,
        "verbose": parsed.verbose,
        "quiet": parsed.quiet,
        "force": parsed.force,
        "stdin": parsed.stdin,
        "code": parsed.code,
        "output": parsed.output,
        "output_overwrite": parsed.output_overwrite,
        "output_append": parsed.output_append,
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
    """Parse CLI arguments and execute a translator.

    This exits the program using `sys.exit` in case of any error, invalid
    input, validation failure, etc. It is therefore not recommended to use this
    function for anything but direct execution of this translator.

    This processes and translates the input in the following steps:

    1. Parse the command-line arguments.
    2. Configure the logger for this package.
    3. Validate the provided input using the PyThia linter, in case any
       error-level (or higher) diagnostics is found, abort.
    4. Translate the code to the given target language/framework.
    5. Output the results according to the instructions.
    """
    parsed = _parse_arguments(arguments)

    configure_logger(
        Verbosity.QUIET
        if parsed["quiet"]
        else Verbosity.VERBOSE
        if parsed["verbose"]
        else Verbosity.NORMAL
    )

    # Reading from `stdin` twice (linter & translator) is not possible,
    # therefore, read the code manually.
    if parsed["stdin"] and not parsed["force"]:
        try:
            code = sys.stdin.read()
        except OSError:
            log.fatal("Failed to read from standard input.")
            sys.exit(ExitCode.READ_ERROR)
        else:
            parsed["stdin"] = False
            parsed["code"] = code

    # Validate input.
    if not parsed["force"]:
        log.debug("Running the linter.")
        linter = default_probabilistic_program_linter()
        if source := parsed["file"]:
            diagnostics = linter.lint_file(source)
        elif parsed["stdin"]:  # should be redundant.
            diagnostics = linter.lint_stdin()
        elif source := parsed["code"]:
            diagnostics = linter.lint_code(source)
        else:
            log.fatal("Did not receive any code or code-source")
            sys.exit(ExitCode.INVALID_ARGUMENTS)
        if linter.found_code_outside():
            log.error(
                "Validation before translation failed"
                ", found additional code besides the model(s)."
            )
            sys.exit(ExitCode.VALIDATION_ERROR)
        elif any(
            diagnostic.severity >= Severity.ERROR for diagnostic in diagnostics
        ):
            log.error("Validation before translation failed.")
            sys.exit(ExitCode.VALIDATION_ERROR)

    # Translate.
    translator = TRANSLATORS.get(parsed["target"])
    if translator is None:
        log.fatal(f"Unknown translation target specified: {parsed['target']}.")
        sys.exit(ExitCode.INVALID_ARGUMENTS)
    if source := parsed["file"]:
        translation = translator.translate_file(source)
    elif parsed["stdin"]:
        translation = translator.translate_stdin()
    elif source := parsed["code"]:
        translation = translator.translate_code(source)
    else:
        log.fatal("Did not receive any code or code-source")
        sys.exit(ExitCode.INVALID_ARGUMENTS)
    if translation is None:
        log.info("Translator failed, could not translate the provided code.")
        sys.exit(ExitCode.TRANSLATION_ERROR)
    translation = translation.strip("\n") + "\n"

    # Output properly.
    log.info(
        "Translator ran successfully, %d character(s)"
        " and %d line(s) translated.",
        len(translation),
        translation.count("\n"),
    )
    if (
        parsed["output"]
        or parsed["output_overwrite"]
        or parsed["output_append"]
    ):
        path, mode = (
            (parsed["output"], "x")
            if parsed["output"]
            else (parsed["output_overwrite"], "w")
            if parsed["output_overwrite"]
            else (parsed["output_append"], "a")
        )
        try:
            file = Path(path)
            with file.open(mode) as stream:
                stream.write(translation)
        except FileExistsError:
            log.fatal("Output file '%s' already exists, aborting.", path)
        except OSError:
            log.fatal("Failed writing to '%s', aborting.", path)
        else:
            log.info("Translation successfully written to file: %s.", path)
    else:
        if not parsed["quiet"]:
            print()  # buffer between logging and results.
        print(translation, end="")


if __name__ == "__main__":
    main()
