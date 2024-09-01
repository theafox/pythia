"""A translator for probabilistic programs.

This module provides a general purpose translator class which may be used with
custom mappings for a spectrum of use-cases. Default implementations and a
CLI-interface are provided which may be used to translate code conforming to
the specifications of the PyThia Meta-Probabilistic-Programming-Language into
the frameworks Gen, Turing, and Pyro.

Usage:
    To use the CLI tool of this module, run this file using Python with the
    appropriate options like:

        $ python3 translator.py -f -o output.txt Gen test.py
        Translator ran successfully, 92 character(s) and 7 line(s) translated.
        Translation successfully written to file: output.txt.

        $ python3 translator.py -v Pyro test.py
        * Reading file: test.py.
        * Parsing code: import sys\n\ndef model(data….
        * No mapping found for node: Module(body=[FunctionDef(….
        * Mapping found for node: FunctionDef(name='model',….
        …

    In case the script exits with an error, the exit code indicates the type of
    error. See `ExitCode` for further details on the specific exit codes.

Options:
    - `h`/`--help` for a help message (no execution of the translator); either
    - `-v` / `--verbose` to print debugging messages or
    - `-q` / `--quiet` to suppress anyything but fatal errors and the results;
    - `-f`/`--force` to force translation, regardless of any code-validation;
    - the target language/framework for translation; either
    - the filepath to the code,
    - `--stdin` to read the code from standard-input (`stdin`), or
    - `-c`/`--code` to pass in code directly in the CLI; and either
    - `-o`/`--output` to output to a file, with an error if it already exists,
    - `--output-overwrite` to overwrite the potentially existing file, or
    - `--output-append` to append to a potentially existing file.

Attributes:
    Translator: This class represents a general translator. By specifying
        mappings and other potential dependencies, the translator may be suited
        to the required use-case.
    ExitCode: An enumeration representing the different possible exit codes.
    default_julia_translator: This provides the default translator for the
        Julia programming language. However, more specific aspects requiring
        knowledge about target frameworks are missing.
    default_gen_translator: This provides the default translator for the Gen
        framework.
    default_turing_translator: This provides the default translator for the
        Turing framework.
    default_python_translator: This provides the default translator for the
        Python programming language. However, more specific aspects requiring
        knowledge about target frameworks are missing.
    default_pyro_translator: This provides the default translator for the Pyro
        framework.
    main: This function includes the setup for the CLI functionality, i.e. the
        specifications of the CLI flags, parsing of the input and running of
        the default probabilistic program translator for PyThia.

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
Version: 0.1.0
Status: In Development
"""

import ast
import logging as log
import sys
from enum import IntEnum
from typing import Any, Callable, Iterable, Mapping, Sequence, override

import mappings.julia as julia_mappings
import mappings.julia.gen as gen_mappings
import mappings.julia.turing as turing_mappings
import mappings.python as python_mappings
import mappings.python.pyro as pyro_mappings
from context import Context
from mappings import BaseMapping, MappingError


class ExitCode(IntEnum):
    """An enumeration which defines exit codes.

    Attributes:
        INVALID_ARGUMENTS: The user provided invalid arguments.
        READ_ERROR: An error occured while reading the input.
        PARSE_ERROR: An error occured while parsing the input.
        TRANSLATION_ERROR: The translation attempt resulted in an error.
        NOT_YET_IMPLEMENTED: The requested feature is not yet implemented.
    """

    # User generated and input errors.
    INVALID_ARGUMENTS = 10
    READ_ERROR = 11
    PARSE_ERROR = 12
    # Runtime errors.
    TRANSLATION_ERROR = 20
    NOT_YET_IMPLEMENTED = 21  # TODO: remove me.


def _display(item: str | ast.AST, maximum_length: int = 25) -> str:
    """Convert the item to a readable representation.

    This is intended to be used for logging. It escapes special characters such
    as `\\t` and limits the maximum length of the string. In case an `ast` node
    is given, dump it to make it readable.

    Args:
        item: The item to make readable.
        maximum_length: The maximum length of the resulting string.

    Returns:
        A readable representation of the given item.
    """

    message = item if isinstance(item, str) else ast.dump(item)
    message = message.encode("unicode_escape", "backslashreplace").decode()
    if len(message) > maximum_length:
        message = f"{message[:maximum_length]}…"
    return message


class Translator:
    """A general purpose translator to translate Python code.

    The current implementation translates the entire code passed to it.
    Therefore, seperating dead-code from code to be translated is the user's
    responsibility.

    The architecture of this translator was kept rather simple, each mapping
    given during instantiation maps a node they are assigned to and may
    influence other nodes only in a limited capacity. (Primarily child-nodes,
    since no explicit functionanilty is provided to access siblings, parents,
    or similar traversal of the abstract syntax tree.) It is therefore intended
    to be used with simpler translations where the original and target code
    resemble each other in their semantic meaning and general structure.

    Attributes:
        mappings: The mapping rules to use for translation.
        preamble: Function which allows placing code before the mapping rules
            are applied.
        postamble: Function which allows placing code after the mapping rules
            are applied.
        validate_node: Function which validates the node to translate. In case
            anything but `True` is returned, that is interpreted as an error.
            Moreover, if a string or multiple are returned, they are
            interpreted as error messasges. If validation fails, no
            translation is attempted.
    """

    # Hide the traversal mechanism from the public eye. Moreover, this prevents
    # confusion between `translate(_file|_code|_stdin)?` and `visit` by the
    # user and inside mapping definitions.
    class _TranslatingTraverser(ast.NodeVisitor):
        """A node traverser used for translation.

        Note that this class is intended to be used for one singular traversal
        of a node tree. It is not intended for rerunning on a new tree, use a
        new instance in that case.

        Attributes:
            mappings: The mapping rules to use for translation.
            context: `Context` object used during the traversal.
        """

        def __init__(
            self,
            mappings: Mapping[type[ast.AST], type[BaseMapping]],
            **kwargs: Any,
        ) -> None:
            super().__init__(**kwargs)
            self.mappings = mappings
            self.context = Context(self)

        @override
        def visit(self, node: ast.AST) -> str:
            """Map the node through traversal using the registered mappings.

            This class is overridden from the parent class. It will be called
            whenever a node is encountered during the walk throug the tree. For
            this reason it is not recommended to subclass this and/or add any
            `visit_*` methods.

            Args:
                node: The node to map.

            Raises:
                MappingError: In case a registered mapping encounters a fatal
                    error, it is not caught and instead passed on.

            Returns:
                The mapping of the provided node.
            """

            if mapping := self.mappings.get(type(node)):
                log.debug(f"Mapping found for node: {_display(node)}.")
                return mapping.map(
                    node, self.context
                )  # pass on `MappingError`
            else:
                log.debug(f"No mapping found for node: {_display(node)}.")
                # This advances further into the tree (child-nodes).
                return str(super().generic_visit(node))

    @override
    def __init__(
        self,
        mappings: Mapping[type[ast.AST], type[BaseMapping]],
        preamble: Callable[[Context], None] = lambda _: None,
        postamble: Callable[[Context], None] = lambda _: None,
        /,
        validate_node: Callable[
            [ast.AST], bool | str | Iterable[str]
        ] = lambda _: True,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.mappings = mappings
        self.preamble = preamble
        self.postamble = postamble
        self.validate_node = validate_node

    def translate(self, node: ast.AST) -> str | None:
        """Translate the provided node.

        Before any translation attempt this checks whether the provided node is
        valid under the syntax restrictions outlined for _PyThia_ by using the
        injected `validate_node` dependency. If validation fails, no
        translation is attempted.

        Args:
            node: The node on which to run the translator on.

        Returns:
            The translated code or `None` in case of an error.
        """

        diagnosis = self.validate_node(node)
        if diagnosis is not True:
            log.error("Validation of the node before translation failed…")
            if diagnosis is not False:
                diagnosis = (
                    [diagnosis]
                    if isinstance(diagnosis, str)
                    else list(diagnosis)
                )
                log.debug("Validation error(s): " + "; ".join(diagnosis))
            return None

        traverser = self._TranslatingTraverser(self.mappings)
        try:
            with traverser.context.in_preamble() as preamble:
                self.preamble(preamble)
            traverser.visit(node)
            with traverser.context.in_postamble() as postamble:
                self.postamble(postamble)
        except MappingError as error:
            log.error(error.message)
            return None
        else:
            return traverser.context.consolidated()

    def translate_code(self, code: str) -> str | None:
        """Translate the provided code.

        This checks whether the provided node is valid under the syntax
        restrictions outlined for _PyThia_ by using
        `Translator.validate_node`. In case anything but `True` is returned,
        that is interpreted as an error. Moreover, if a string or multiple are
        returned, they are interpreted as error messasges. If validation
        fails, no translation is attempted.

        Args:
            code: The code on which to run the translator on.

        Returns:
            The translated code or `None` in case of an error.
        """

        log.debug(f"Parsing code: {_display(code)}.")
        try:
            node = ast.parse(code)
        except (SyntaxError, ValueError):
            log.fatal(f"Could not parse code: {_display(code)}.")
            exit(ExitCode.PARSE_ERROR)
        return self.translate(node)

    def translate_file(self, path: str) -> str | None:
        """Translate the file located at the provided file-path.

        This checks whether the provided node is valid under the syntax
        restrictions outlined for _PyThia_ by using
        `Translator.validate_node`. In case anything but `True` is returned,
        that is interpreted as an error. Moreover, if a string or multiple are
        returned, they are interpreted as error messasges. If validation
        fails, no translation is attempted.

        Args:
            path: The file-path pointing to the file on which to run the
                translator.

        Returns:
            The translated code or `None` in case of an error.
        """

        log.debug(f"Reading file: {_display(path)}.")
        try:
            with open(path, "r") as file:
                code = file.read()
        except IOError:
            log.fatal(f"Could not read the file: {_display(path)}.")
            exit(ExitCode.READ_ERROR)
        return self.translate_code(code)

    def translate_stdin(self) -> str | None:
        """Translate the input from standard-input (`stdin`).

        This checks whether the provided node is valid under the syntax
        restrictions outlined for _PyThia_ by using
        `Translator.validate_node`. In case anything but `True` is returned,
        that is interpreted as an error. Moreover, if a string or multiple are
        returned, they are interpreted as error messasges. If validation
        fails, no translation is attempted.

        Returns:
            The translated code or `None` in case of an error.
        """

        log.debug("Reading from `stdin`.")
        try:
            code = sys.stdin.read()
        except IOError:
            log.fatal("Could not read from stdin.")
            exit(ExitCode.READ_ERROR)
        return self.translate_code(code)


def default_julia_translator() -> Translator:
    """Construct a default translator for Julia.

    This includes all general mappings for the Julia programming language to
    conform to the specifications of PyThia. However, since more specific
    aspects of PyThia may not be translated without knowledge about the
    specific target framework, some mappings are missing. Therefore, this is
    akin to a abstract base for different frameworks inside Julia.

    Returns:
        A translator which may be used to translate PyThia code into general
        Julia code.
    """

    return Translator(
        {
            # Statements.
            ast.FunctionDef: julia_mappings.FunctionMapping,
            ast.If: julia_mappings.IfMapping,
            ast.While: julia_mappings.WhileLoopMapping,
            ast.For: julia_mappings.ForLoopMapping,
            ast.Assign: julia_mappings.AssignmentMapping,
            ast.Expr: julia_mappings.StandaloneExpressionMapping,
            ast.Return: julia_mappings.ReturnMapping,
            ast.Continue: julia_mappings.ContinueMapping,
            ast.Break: julia_mappings.BreakMapping,
            # Expressions.
            ast.Tuple: julia_mappings.TupleMapping,
            ast.List: julia_mappings.ListMapping,
            ast.Attribute: julia_mappings.AttributeMapping,
            ast.Subscript: julia_mappings.IndexingMapping,
            ast.Call: julia_mappings.CallMapping,
            ast.BinOp: julia_mappings.BinaryOperatorsMapping,
            ast.Compare: julia_mappings.BinaryOperatorsMapping,
            ast.BoolOp: julia_mappings.BinaryOperatorsMapping,
            ast.UnaryOp: julia_mappings.UnaryOperatorsMapping,
            ast.Constant: julia_mappings.ConstantMapping,
            ast.Name: julia_mappings.NameMapping,
        }
    )


def default_gen_translator() -> Translator:
    """Construct a default translator for Gen.

    This uses the general mappings outlined in `default_julia_translator`.
    See the implementation and potential further documentation for the
    mappings specific to Gen.

    Returns:
        A translator which may be used to translate PyThia code into the Gen
        framework.
    """

    julia_translator = default_julia_translator()
    julia_translator.preamble = gen_mappings.preamble
    julia_translator.mappings = dict(julia_translator.mappings) | {
        ast.FunctionDef: gen_mappings.FunctionMapping,
        ast.Call: gen_mappings.CallMapping,
    }
    return julia_translator


def default_turing_translator() -> Translator:
    """Construct a default translator for Turing.

    This uses the general mappings outlined in `default_julia_translator`.
    See the implementation and potential further documentation for the
    mappings specific to Turing.

    Returns:
        A translator which may be used to translate PyThia code into the Turing
        framework.
    """

    julia_translator = default_julia_translator()
    julia_translator.preamble = turing_mappings.preamble
    julia_translator.mappings = dict(julia_translator.mappings) | {
        ast.FunctionDef: turing_mappings.FunctionMapping,
        ast.Assign: turing_mappings.AssignmentMapping,
        ast.Call: turing_mappings.CallMapping,
    }
    return julia_translator


def default_python_translator() -> Translator:
    """Construct a default translator for Python.

    This includes all general mappings for the Python programming language to
    conform to the specifications of PyThia. However, since more specific
    aspects of PyThia may not be translated without knowledge about the
    specific target framework, some mappings are missing. Therefore, this is
    akin to a abstract base for different frameworks inside Python.

    Returns:
        A translator which may be used to translate PyThia code into general
        Python code.
    """

    return Translator(
        {
            # Statements.
            ast.FunctionDef: python_mappings.FunctionMapping,
            ast.If: python_mappings.IfMapping,
            ast.While: python_mappings.WhileLoopMapping,
            ast.For: python_mappings.ForLoopMapping,
            ast.Assign: python_mappings.AssignmentMapping,
            ast.Expr: python_mappings.StandaloneExpressionMapping,
            ast.Return: python_mappings.ReturnMapping,
            **{
                target: python_mappings.GenericStatementMapping
                for target in (ast.Continue, ast.Break)
            },
            # Expressions.
            ast.Tuple: python_mappings.TupleMapping,
            ast.List: python_mappings.ListMapping,
            ast.Attribute: python_mappings.AttributeMapping,
            ast.Subscript: python_mappings.IndexingMapping,
            ast.BinOp: python_mappings.BinaryOperatorsMapping,
            ast.Compare: python_mappings.BinaryOperatorsMapping,
            ast.BoolOp: python_mappings.BinaryOperatorsMapping,
            ast.UnaryOp: python_mappings.UnaryOperatorsMapping,
            **{
                target: python_mappings.GenericExpressionMapping
                for target in (ast.Constant, ast.Name)
            },
        }
    )


def default_pyro_translator() -> Translator:
    """Construct a default translator for Pyro.

    This uses the general mappings outlined in `default_python_translator`.
    See the implementation and potential further documentation for the
    mappings specific to Pyro.

    Returns:
        A translator which may be used to translate PyThia code into the Pyro
        framework.
    """

    python_translator = default_python_translator()
    python_translator.preamble = pyro_mappings.preamble
    python_translator.mappings = dict(python_translator.mappings) | {
        ast.Call: pyro_mappings.CallMapping
    }
    return python_translator


def main(arguments: Sequence[str] | None = None) -> None:
    """Parse CLI arguments and execute a translator.

    This uses `argparse` to decypher any arguments. Valid arguments are:
    - `h`/`--help` for a help message (no execution of the translator); either
    - `-v` / `--verbose` to print debugging messages or
    - `-q` / `--quiet` to suppress anyything but fatal errors and the results;
    - `-f`/`--force` to force translation, regardless of any code-validation;
    - the target language/framework for translation; either
    - the filepath to the code,
    - `--stdin` to read the code from standard-input (`stdin`), or
    - `-c`/`--code` to pass in code directly in the CLI; and either
    - `-o`/`--output` to output to a file, with an error if it already exists,
    - `--output-overwrite` to overwrite the potentially existing file, or
    - `--output-append` to append to a potentially existing file.
    """

    import argparse

    translators = {
        "pyro": default_pyro_translator(),
        "gen": default_gen_translator(),
        "turing": default_turing_translator(),
    }

    parser = argparse.ArgumentParser(
        description="Translate probabilistic programms from PyThia into "
        + ", ".join(translators.keys())[::-1].replace(",", "ro ,", 1)[::-1]
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
        choices=translators.keys(),
        type=str.lower,
        help="language/framework to translate the code to",
    )
    code_origin = parser.add_mutually_exclusive_group(required=True)
    code_origin.add_argument(
        "filepath",
        nargs="?",
        help="file to run the translator on",
    )
    code_origin.add_argument(
        "--stdin",
        action="store_true",
        help="read the code from stdin",
    )
    code_origin.add_argument(
        "-c",
        "--code",
        type=str,
        help="the code to lint",
    )
    code_destination = parser.add_mutually_exclusive_group()
    code_destination.add_argument(
        "-o",
        "--output",
        type=str,
        help="file to write the output to (error if it already exists)",
    )
    code_destination.add_argument(
        "--output-overwrite",
        type=str,
        help="file to write the output to (overwriting if it already exists)",
        dest="output_overwrite",
    )
    code_destination.add_argument(
        "--output-append",
        type=str,
        help="file to write the output to (appending if it already exists)",
        dest="output_append",
    )
    args = parser.parse_args(arguments)

    # Use multiple handlers, to allow redirecting the output if required and
    # prepending messages with indicators of logging or warning messages.
    warning = log.StreamHandler(sys.stdout)
    warning.addFilter(lambda record: log.ERROR <= record.levelno)
    warning.setFormatter(log.Formatter("! %(message)s"))
    if args.quiet:
        log.basicConfig(level=log.FATAL, handlers=(warning,))
    else:
        standard = log.StreamHandler(sys.stdout)
        standard.addFilter(
            lambda record: log.DEBUG < record.levelno < log.ERROR
        )
        standard.setFormatter(log.Formatter("%(message)s"))
        if not args.verbose:
            log.basicConfig(level=log.INFO, handlers=(warning, standard))
        else:
            verbose = log.StreamHandler(sys.stdout)
            verbose.addFilter(lambda record: record.levelno <= log.DEBUG)
            verbose.setFormatter(log.Formatter("* %(message)s"))
            log.basicConfig(
                level=log.DEBUG, handlers=(warning, standard, verbose)
            )

    translator = translators.get(args.target)
    if translator is None:
        log.fatal(f"Unknown translation target specified: {args.target}.")
        exit(ExitCode.INVALID_ARGUMENTS)
    if not args.force:
        # TODO: Integrate the default linter for PyThia.
        log.fatal(
            "The linter is not yet available, "
            "please use `-f` or `--force` for the time being."
        )
        exit(ExitCode.NOT_YET_IMPLEMENTED)
    translation = None
    if args.filepath:
        translation = translator.translate_file(args.filepath)
    elif args.stdin:
        translation = translator.translate_stdin()
    elif args.code:
        translation = translator.translate_code(args.code)
    else:
        log.fatal("Did not receive any code or code-source")
        exit(ExitCode.INVALID_ARGUMENTS)
    if translation is None:
        log.info("Translator failed, could not translate the provided code.")
        exit(ExitCode.TRANSLATION_ERROR)
    translation = translation.strip("\n") + "\n"

    log.info(
        f"Translator ran successfully, {len(translation)} character(s)"
        f" and {translation.count("\n")} line(s) translated."
    )
    if args.output or args.output_overwrite or args.output_append:
        path, mode = (
            (args.output, "x")
            if args.output
            else (
                (args.output_overwrite, "w")
                if args.output_overwrite
                else (args.output_append, "a")
            )
        )
        try:
            with open(path, mode) as file:
                file.write(translation)
        except FileExistsError:
            log.fatal(f"Output file '{path}' already exists, aborting.")
        else:
            log.info(f"Translation successfully written to file: {path}.")
    else:
        if not args.quiet:
            print()
        print(translation, end="")


if __name__ == "__main__":
    main()
