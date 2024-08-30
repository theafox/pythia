import ast
import logging as log
import sys
from enum import IntEnum
from typing import Any, Callable, Iterable, Mapping, override

import mappings.julia as julia_mappings
import mappings.julia.gen as gen_mappings
import mappings.julia.turing as turing_mappings
import mappings.python as python_mappings
import mappings.python.pyro as pyro_mappings
from context import Context
from mappings import BaseMapping, MappingError


class ExitCode(IntEnum):
    # User generated and input errors.
    INVALID_ARGUMENTS = 10
    READ_ERROR = 11
    PARSE_ERROR = 12
    # Runtime errors.
    TRANSLATION_ERROR = 20
    NOT_YET_IMPLEMENTED = 21  # TODO: remove me.


def _display(item: str | ast.AST, maximum_length: int = 25) -> str:
    message = item if isinstance(item, str) else ast.dump(item)
    message = message.encode("unicode_escape", "backslashreplace").decode()
    if len(message) > maximum_length:
        message = f"{message[:maximum_length]}…"
    return message


class Translator(ast.NodeVisitor):
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

        self._context = Context(self)

    @override
    def visit(self, node: ast.AST) -> str:
        if mapping := self.mappings.get(type(node)):
            log.debug(f"Mapping found for node: {_display(node)}.")
            return mapping.map(node, self._context)
        else:
            log.debug(f"No mapping found for node: {_display(node)}.")
            return str(super().generic_visit(node))

    def translate(self, node: ast.AST) -> str | None:
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

        self._context = Context(self)
        try:
            with self._context.in_preamble() as preamble:
                self.preamble(preamble)
            self.visit(node)
            with self._context.in_postamble() as postamble:
                self.postamble(postamble)
        except MappingError as error:
            log.error(error.message)
            return None
        else:
            return self._context.consolidated()

    def translate_code(self, code: str) -> str | None:
        log.debug(f"Parsing code: {_display(code)}.")
        try:
            node = ast.parse(code)
        except (SyntaxError, ValueError):
            log.fatal(f"Could not parse code: {_display(code)}.")
            exit(ExitCode.PARSE_ERROR)
        return self.translate(node)

    def translate_file(self, path: str) -> str | None:
        log.debug(f"Reading file: {_display(path)}.")
        try:
            with open(path, "r") as file:
                code = file.read()
        except IOError:
            log.fatal(f"Could not read the file: {_display(path)}.")
            exit(ExitCode.READ_ERROR)
        return self.translate_code(code)

    def translate_stdin(self) -> str | None:
        log.debug("Reading from `stdin`.")
        try:
            code = sys.stdin.read()
        except IOError:
            log.fatal("Could not read from stdin.")
            exit(ExitCode.READ_ERROR)
        return self.translate_code(code)


def default_julia_translator() -> Translator:
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
    julia_translator = default_julia_translator()
    julia_translator.preamble = gen_mappings.preamble
    julia_translator.mappings = dict(julia_translator.mappings) | {
        ast.FunctionDef: gen_mappings.FunctionMapping,
        ast.Call: gen_mappings.CallMapping,
    }
    return julia_translator


def default_turing_translator() -> Translator:
    julia_translator = default_julia_translator()
    julia_translator.preamble = turing_mappings.preamble
    julia_translator.mappings = dict(julia_translator.mappings) | {
        ast.FunctionDef: turing_mappings.FunctionMapping,
        ast.Assign: turing_mappings.AssignmentMapping,
        ast.Call: turing_mappings.CallMapping,
    }
    return julia_translator


def default_python_translator() -> Translator:
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
    python_translator = default_python_translator()
    python_translator.preamble = pyro_mappings.preamble
    python_translator.mappings = dict(python_translator.mappings) | {
        ast.Call: pyro_mappings.CallMapping
    }
    return python_translator
