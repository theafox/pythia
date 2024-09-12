"""The main components of the `translator` module.

The `translator` module is designed to provide the ability to translate Python
code into other languages/frameworks. This file provides the main components of
this functionality.

Usage:
    For usage in a script see the package documentation (`__init__.py`). For
    usage as a CLI tool see the module documentation (`__main__.py`).

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

import ast
import logging
import sys
from enum import IntEnum
from typing import Any, Callable, Iterable, Mapping, override

import translator.mappings.julia as julia_mappings
import translator.mappings.julia.gen as gen_mappings
import translator.mappings.julia.turing as turing_mappings
import translator.mappings.python as python_mappings
import translator.mappings.python.pyro as pyro_mappings
from translator.context import Context
from translator.mappings import BaseMapping, MappingError, MappingWarning

log = logging.getLogger(__name__)


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
    r"""Convert the item to a readable representation.

    This is intended to be used for logging. It escapes special characters such
    as `\t` and limits the maximum length of the string. In case an `ast` node
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
    Therefore, separating dead-code from code to be translated is the user's
    responsibility.

    The architecture of this translator was kept rather simple, each mapping
    given during instantiation maps a node they are assigned to and may
    influence other nodes only in a limited capacity. (Primarily child-nodes,
    since no explicit functionality is provided to access siblings, parents,
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
            interpreted as error messages. If validation fails, no
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
            whenever a node is encountered during the walk through the tree.
            For this reason it is not recommended to subclass this and/or add
            any `visit_*` methods.

            Args:
                node: The node to map.

            Raises:
                MappingError: In case a registered mapping encounters a fatal
                    error, it is not caught and instead passed on.

            Returns:
                The mapping of the provided node.
            """
            if mapping := self.mappings.get(type(node)):
                try:
                    mapped = mapping.map(node, self.context)
                except MappingError as error:
                    raise error
                except MappingWarning as warning:
                    cause = warning.message.removesuffix(".")
                    log.warning(
                        "Mapping failed for node-type `%s`: %s.",
                        type(node).__name__,
                        cause,
                    )
                else:
                    if mapped is not None:
                        return mapped
            else:
                # This advances further into the tree (child-nodes).
                mapped = super().generic_visit(node)
                if mapped:
                    return mapped
            return str(node)

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
                log.debug("Validation error(s): %s.", "; ".join(diagnosis))
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
        returned, they are interpreted as error messages. If validation
        fails, no translation is attempted.

        Args:
            code: The code on which to run the translator on.

        Returns:
            The translated code or `None` in case of an error.
        """
        log.debug("Parsing code: %s.", _display(code))
        try:
            node = ast.parse(code)
        except (SyntaxError, ValueError):
            log.fatal("Could not parse code: %s.", _display(code))
            exit(ExitCode.PARSE_ERROR)
        return self.translate(node)

    def translate_file(self, path: str) -> str | None:
        """Translate the file located at the provided file-path.

        This checks whether the provided node is valid under the syntax
        restrictions outlined for _PyThia_ by using
        `Translator.validate_node`. In case anything but `True` is returned,
        that is interpreted as an error. Moreover, if a string or multiple are
        returned, they are interpreted as error messages. If validation
        fails, no translation is attempted.

        Args:
            path: The file-path pointing to the file on which to run the
                translator.

        Returns:
            The translated code or `None` in case of an error.
        """
        log.debug("Reading file: %s.", _display(path))
        try:
            with open(path, "r") as file:
                code = file.read()
        except IOError:
            log.fatal("Could not read the file: %s.", _display(path))
            exit(ExitCode.READ_ERROR)
        return self.translate_code(code)

    def translate_stdin(self) -> str | None:
        """Translate the input from standard-input (`stdin`).

        This checks whether the provided node is valid under the syntax
        restrictions outlined for _PyThia_ by using
        `Translator.validate_node`. In case anything but `True` is returned,
        that is interpreted as an error. Moreover, if a string or multiple are
        returned, they are interpreted as error messages. If validation
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
