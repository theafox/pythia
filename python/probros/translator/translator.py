import ast
from typing import Callable, Mapping, override

import mappings.julia as julia_mappings
import mappings.julia.gen as gen_mappings
import mappings.python as python_mappings
import mappings.python.pyro as pyro_mappings
from context import Context
from mappings import BaseMapping, MappingError

_PARSE_ERROR_CODE = 10
_READ_ERROR_CODE = 20


class Translator(ast.NodeTransformer):
    @override
    def __init__(
        self,
        mappings: Mapping[type[ast.AST], type[BaseMapping]],
        preamble: Callable[[Context], None] = lambda _: None,
        postamble: Callable[[Context], None] = lambda _: None,
    ):
        super().__init__()
        self.mappings = mappings
        self.preamble = preamble
        self.postamble = postamble
        self._context = Context(self)

    @override
    def visit(self, node: ast.AST) -> ast.AST | str:
        return (
            mapping.map(node, self._context)
            if (mapping := self.mappings.get(type(node)))
            else super().generic_visit(node)
        )

    def translate(self, node: ast.AST) -> str:
        self._context = Context(self)
        try:
            with self._context.in_preamble() as preamble:
                self.preamble(preamble)
            self.visit(node)
            with self._context.in_postamble() as postamble:
                self.postamble(postamble)
        except MappingError as error:
            return error.message  # TODO: implement proper logging
        else:
            return self._context.consolidated()

    def translate_code(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except (SyntaxError, ValueError):
            exit(_PARSE_ERROR_CODE)
        return self.translate(tree)

    def translate_file(self, path: str) -> str:
        try:
            with open(path, "r") as file:
                code = file.read()
        except IOError:
            exit(_READ_ERROR_CODE)
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
