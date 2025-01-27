"""This definse mappings for a `choicemap` construction in Gen.

Note that using this requires models to have an independent logic for samples
and observe statements. Since this cuts out any `sample`, `factor`, etc.
statements having any variables or control-flow constructs dependent on that,
will result in an invalid `choicemap` aggregation.
"""

import ast
from typing import Callable, ClassVar, override

from translator import Context
from translator.mappings.julia import (
    AssignmentMapping as BaseAssignmentMapping,
)
from translator.mappings.julia import FunctionMapping as BaseFunctionMapping
from translator.mappings.julia import ReturnMapping as BaseReturnMapping
from translator.mappings.julia import (
    StandaloneExpressionMapping as BaseStandaloneExpressionMapping,
)
from translator.mappings.julia.gen import CallMapping as GenCallMapping
from translator.mappings.utils import get_name, organize_arguments


def preamble(context: Context) -> None:
    context.line("__observe_constraints = Gen.choicemap()")


class FunctionMapping(BaseFunctionMapping):
    name = "__choicemap_aggregation"


class AssignmentMapping(BaseAssignmentMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case (
                ast.Assign(value=ast.Call() as function)
                | ast.AnnAssign(value=ast.Call() as function)
            ) if get_name(function) == "sample":
                return None
            case _:
                return super().map(node, context)


class StandaloneExpressionMapping(BaseStandaloneExpressionMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Expr(value=ast.Call() as function) if (
                get_name(function) != "observe"
            ):
                return None
            case _:
                return super().map(node, context)


class ReturnMapping(BaseReturnMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case ast.Return():
                context.line("return")
                return None
            case _:
                return super().map(node, context)


class CallMapping(GenCallMapping):
    @staticmethod
    def _observe(node: ast.Call, context: Context) -> str:
        arguments = organize_arguments(
            node.args,
            node.keywords,
            argument_defaults=[ast.Constant(0)],
            keyword_argument_defaults=[
                (2, "address", lambda: ast.Constant(Context.unique_address())),
            ],
        )
        value, address = list(arguments)[:2]
        value = context.translator.visit(value)
        address = context.translator.visit(address)
        return f"__observe_constraints[{address}] = {value}"

    mappings: ClassVar[dict[str, Callable[[ast.Call, Context], str]]] = {
        **GenCallMapping.mappings,
        "observe": _observe,
    }
