"""A linter for probabilistic programs.

TODO: add specifications!

Example:
    This script may also be used as a CLI tool to lint files according to the
    specifications. When used as a CLI tool, a `-q`/`--quiet` or
    `-v`/`--verbose` flag may be provided to specify the verbosity of the
    logging output. The former restricts it to fatal messages, while the latter
    shows everything logged. To format the output as JSON, the `--json` flag
    may be provided. (This may include more details than the standard output.)
    Additionally, either one positional argument must be provided, a file-path,
    or the code directly via the `-c`/`--code` flag. (View these options using
    the `-h`/`--help` flag.)

        $ python3 linter.py test.py
        Linter ran successfully, received 3 hints.
          51:4: ERROR: Nested functions are not allowed
        …

        $ python3 linter.py -v test.py
        * Received 'test.py'… as a string, try interpreting it as a file-path.
        * Identified 'test.py'… as a file, reading the contents.
        * Parsing 'import probros\n\n\n# This s'… as code.
        …

Attributes:
    Linter: This class represents a general purpose linter. By specifying rules
        and entry-point identifiers, the linter may be suited to the required
        use-case.
    default_probabilistic_program_linter: This returns the default linter for
        probabilistic programs.
    main: This function includes the setup for the CLI functionality, i.e. the
        specifications of the CLI flags, parsing of the input and running of
        the default probabilistic program linter.

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
Version: 0.1.0
Status: In Development
"""

import ast
import logging as log
from typing import Callable, Iterable

import rules
from diagnostic import Diagnostic, Severity

# NOTE: extract this dynamically from `probros` to future-proof for changes?
_DECORATOR_NAME = "probabilistic_program"
_PARSE_ERROR_CODE = 10
_READ_ERROR_CODE = 20


class Linter(ast.NodeVisitor):
    """A general purpose linter to validate python code.

    This linter allows to specify entry-points to code of interest. This
    enables the user to disregard large portions of the code and focus on
    certain aspects of it to lint.

    The current implementation does not enter any further into the syntax tree
    upon analyzing a node which violates rules.

    Note that, the entry-point-node itself is _not_ validated using those
    rules, `analyze_entry_point` may be used for this purpose.

    Analysis on porential entry-points using `analyze_entry_point` checks any
    node outside code of interest. It is therefore independent of the check for
    entry-point nodes and does _not_ guarentee that the passed node is a valid
    entry-point.

    Attributes:
        rules: The rules to apply to code of interest.
        is_entry_point: A function to identify entry-points.
        analyze_entry_point: A function to analyze the entry-point itself.
        diagnostics: The list of currently found diagnostics.
    """

    def __init__(
        self,
        rules: Iterable[type[rules.BaseRule]],
        is_entry_point: Callable[[ast.AST], bool],
        analyze_entry_point: Callable[
            [ast.AST], Iterable[Diagnostic]
        ] = lambda *args, **kwargs: [],
        **kwargs,
    ):
        """Initialize the linter.

        Args:
            rules: The rules to apply to code of interest.
            is_entry_point: A function to identify entry-points.
            analyze_entry_point: A function to analyze the entry-point itself.
            **kwargs: Any additional key-word-arguments will be handed to the
                super-class initialization.
        """

        super().__init__(**kwargs)

        self.rules = rules
        self.is_entry_point = is_entry_point
        self.analyze_entry_point = analyze_entry_point

        self.diagnostics: list[Diagnostic] = []
        self._entered: bool = False

    def generic_visit(self, node: ast.AST) -> None:
        """Identify entry-points and apply rules.

        This class is overridden from the parent class. It will be called
        whenever a node is encountered during the walk throug the tree. For
        this reason it is not recommended to subclass this and add any
        `visit_*` methods.

        Args:
            node: The node to identify or analyze.
        """

        # Outside code of interest…
        if not self._entered:
            self.diagnostics += self.analyze_entry_point(node)
            if not self.is_entry_point(node):
                super().generic_visit(node)
            else:
                log.debug(f"Found admissible node {ast.dump(node)[:25]}….")
                self._entered = True
                super().generic_visit(node)
                self._entered = False
            return

        # Inside code of interest…
        diagnostics: list[Diagnostic] = [
            diagnostic
            for diagnostic in [rule.check(node) for rule in self.rules]
            if diagnostic
        ]
        if diagnostics:
            log.debug(
                f"Rules ({len(diagnostics)}) were applicable:"
                f" {*diagnostics, }"
            )
            self.diagnostics += diagnostics
        else:
            # Only enter further into nodes which do _not_ violate any rules.
            super().generic_visit(node)

    def lint(self, tree: ast.AST) -> list[Diagnostic]:
        """Lint the provided node.

        Args:
            tree: The node on which to run the linter on.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug(f"Linting tree {ast.dump(tree)[:25]!a}….")

        self.diagnostics = []
        self.visit(tree)
        log.debug(
            f"Linting finished, got {len(self.diagnostics)} diagnostic(s)."
        )

        diagnostics: list[Diagnostic] = self.diagnostics
        self.diagnostics = []
        return diagnostics

    def lint_code(self, code: str) -> list[Diagnostic]:
        """Lint the provided code.

        In case of errors while or because of parsing the code, exit the
        program with code `_PARSE_ERROR_CODE`.

        Args:
            code: The code on which to run the linter on.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug(f"Parsing code {code[:25]!a}….")
        try:
            tree: ast.AST = ast.parse(code)
        except (SyntaxError, ValueError):
            log.fatal(f"Could not parse code {code[:25]!a}….")
            exit(_PARSE_ERROR_CODE)
        return self.lint(tree)

    def lint_file(self, path: str) -> list[Diagnostic]:
        """Lint the file located at the provided file-path.

        In case of errors while or because of reading the file, exit the
        program with code `_READ_ERROR_CODE`. And in case of or because of
        parsing the code, with code `_PARSE_ERROR_CODE`.

        Args:
            path: The file-path pointing to the file on which to run the
                linter.

        Returns:
            The diagnostics found by the linter. All diagnostics identified by
            the linter and any runtime errors are logged.
        """

        log.debug(f"Reading file {path[:25]!a}….")
        try:
            with open(path, "r") as file:
                code: str = file.read()
        except IOError:
            log.fatal(f"Could not read file {path[:25]!a}….")
            exit(_READ_ERROR_CODE)
        return self.lint_code(code)


def _is_probabilistic_program_entry_point(node: ast.AST) -> bool:
    """Checks whether or not this declares a probabilistic program.

    Note that this only checks for the string of the function's decorator to
    match `_DECORATOR_NAME` currently, no actual testing is done to ensure the
    origin of the decorator. This may lead to incorrect identification of
    functions in case other decorators share that name.

    Args:
        node: The node to check.

    Returns:
        True if this could be identified as a probabilistic program, False
        otherwise.
    """

    return isinstance(node, ast.FunctionDef) and any(
        isinstance(decorator, ast.Attribute)
        and decorator.attr == _DECORATOR_NAME
        or isinstance(decorator, ast.Name)
        and decorator.id == _DECORATOR_NAME
        for decorator in node.decorator_list
    )


def _analyze_probabilistic_program_entry_point(
    node: ast.AST,
) -> Iterable[Diagnostic]:
    """Analyze the decorators of potential probabilistic program declarations.

    Only decorators of type `Name` and `Attribute` will be recognized, any
    others receive a diagnostic.

    This additionally checks for any decorators on classes and asynchronous
    functions to warn users that their usage is intended for functions only.

    Args:
        node: The function node to analyze.

    Returns:
        A list of diagnostics for all unrecognized decorators.
    """

    if (
        isinstance(node, ast.ClassDef)
        or isinstance(node, ast.AsyncFunctionDef)
    ) and any(
        isinstance(decorator, ast.Attribute)
        and decorator.attr == _DECORATOR_NAME
        or isinstance(decorator, ast.Name)
        and decorator.id == _DECORATOR_NAME
        for decorator in node.decorator_list
    ):
        return [
            Diagnostic.from_node(
                node,
                message="Probabilistic program decorators are intended for"
                " functions only",
                severity=Severity.INFORMATION,
            )
        ]
    elif not isinstance(node, ast.FunctionDef):
        return []

    unrecognized: list[ast.expr] = list(
        filter(
            lambda decorator: not isinstance(
                decorator,
                (ast.Attribute, ast.Name, ast.Call),
            ),
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

    return diagnostics


def default_probabilistic_program_linter() -> Linter:
    """Construct the default linter for probabilistic programs.

    This includes all rules to conform to the specifications of a probabilistic
    program.

    Returns:
        A linter which may be run on any python code to validate any
        probabilistic programs.
    """
    return Linter(
        {
            rules.NoNestedFunctionsRule,
            rules.NoNestedClassesRule,
            rules.NoImportRule,
            rules.NoGlobalOrNonlocalDeclarationRule,
            rules.NoDeleteStatementRule,
            rules.NoTypeAliasRule,
            rules.NoDeconstructorRule,
            rules.NoChainedAssignmentRule,
            rules.RestrictForLoopRule,
            rules.NoWithStatementRule,
            rules.NoMatchRule,
            rules.NoAsynchronousStatementRule,
            rules.NoPassRule,
            rules.NoRaiseExceptionRule,
            rules.NoTryExceptRule,
            rules.NoAssertRule,
            rules.NoWalrusOperatorRule,
            rules.RestrictBinaryOperatorsRule,
            rules.RestrictUnaryOperatorsRule,
            rules.NoLambdaRule,
            rules.NoInlineIfRule,
            rules.NoDictionaryRule,
            rules.NoSetRule,
            rules.NoComprehensionAndGeneratorRule,
            rules.NoAsynchronousExpressionRule,
            rules.NoYieldRule,
            rules.NoFstringRule,
        },
        _is_probabilistic_program_entry_point,
        _analyze_probabilistic_program_entry_point,
    )


def main() -> None:
    """Parse CLI arguments and execute the linter.

    This uses `argparse` to decypher any arguments. Valid arguments are:
    - either `-v` / `--verbose` to print debugging messages or
    - `-q` / `--quiet` to suppress anyything but fatal errors and the results,
    - `--json` to format the output as JSON, and
    - either a filepath as a positional argument, or code usig `-c`/`--code`.
    """

    import argparse
    import sys
    from dataclasses import asdict
    from json import dumps

    parser = argparse.ArgumentParser()
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print verbose messages",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Only print the results",
    )
    code_origin = parser.add_mutually_exclusive_group(required=True)
    code_origin.add_argument(
        "filepath",
        help="File to run the linter on",
        type=str,
        nargs="?",
    )
    code_origin.add_argument("-c", "--code", help="The code to lint", type=str)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the results in JSON format",
    )
    args = parser.parse_args()

    if args.quiet:
        log.basicConfig(level=log.CRITICAL)
    elif args.verbose:
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

    linter: Linter = default_probabilistic_program_linter()
    diagnostics: list[Diagnostic] = []
    if args.filepath:
        diagnostics += linter.lint_file(args.filepath)
    elif args.code:
        diagnostics += linter.lint_code(args.code)
    else:
        return

    log.info(f"Linter ran successfully, got {len(diagnostics)} diagnostic(s).")
    if args.json:
        print(
            dumps(
                {
                    "diagnostics": list(
                        map(
                            lambda diagnostic: asdict(diagnostic),
                            diagnostics,
                        )
                    )
                },
                default=str,
            )
        )
    else:
        # Print as one block.
        print("\n".join(str(diagnostic) for diagnostic in diagnostics))


if __name__ == "__main__":
    main()
