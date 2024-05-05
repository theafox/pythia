import ast
import logging


class Linter(ast.NodeVisitor):
    """A custom linter to traverse the AST tree and identify issues.

    This linter focuses on programs implementing probabilistic programs
    according to the specifications in `docs.ipynb`.

    Attributes:
        errors (list[str]): A list to store found errors
    """

    def __init__(self) -> None:
        """Initialize the linter."""
        self.errors: list[str] = []
        logging.debug(f"Initialized linter with {self.errors=}.")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit and analyze a function definition.

        Args:
            node (ast.FunctionDef): The node to be analyzed.
        """
        self.generic_visit(node)


def lint_code(code: str) -> list[str] | None:
    """Lint the provided python code.

    Args:
        code: The Python code to be linted.

    Returns:
        The errors found by the linter as strings or `None` in case of errors.
        All errors identified by the linter and any runtime errors are logged.
    """

    escaped_snippet = code[:25].encode("unicode_escape").decode()
    logging.debug("Running linter on given code " + f"'{escaped_snippet}…'.")
    linter = Linter()
    try:
        tree = ast.parse(code)
    except ValueError:
        logging.warn("Received invalid data.")
        return None

    linter.visit(tree)
    errors = linter.errors
    logging.info(f"Linter ran successfully, found {len(errors)} errors.")

    return errors


def lint_file(filepath: str) -> list[str] | None:
    """Lint the provided file.

    This currently reads the whole file into memory and parses it afterwards.
    Therefore, this may cause problems with very large files.

    Args:
        code: The path to the file containing the Python code to be linted.

    Returns:
        The errors found by the linter as strings or `None` in case of errors.
        All errors identified by the linter and any runtime errors are logged.
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
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
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
