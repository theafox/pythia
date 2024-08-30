"""This file contains mappings specific for the Gen framework.

Note that this builds on top of the more general mapping provided by
`./syntax.py`.

Each mapping is implemented as a class inheriting from `BaseMapping`.
Therefore, view the documentation of that class in case of changes or
additions.
"""

import ast
from typing import Callable, Iterable

from context import Context

from mappings import MappingError
from mappings.utils import (
    get_function_call_mapping,
    get_name,
    organize_arguments,
)

from .syntax import CallMapping as BaseCallMapping
from .syntax import FunctionMapping as BaseFunctionMapping


def preamble(context: Context) -> None:
    context.line("using Gen")
    context.line("using Distributions")


class FunctionMapping(BaseFunctionMapping):
    macros: Iterable[str] = ["gen"]


class CallMapping(BaseCallMapping):
    @staticmethod
    def _unsupported(node: ast.Call, _: Context) -> str:
        name = get_name(node.func)
        raise MappingError(f"Gen doesn't provide an equivalent for `{name}`.")

    @staticmethod
    def _sample(node: ast.Call, context: Context) -> str:
        arguments = organize_arguments(
            node.args,
            node.keywords,
            argument_defaults=[
                lambda: ast.Constant(Context.unique_address()),
                ast.Call(ast.Name("Dirac"), [ast.Constant(True)], []),
            ],
        )
        argument_strings = [
            context.translator.visit(argument) for argument in arguments
        ]
        address, distribution = argument_strings[:2]
        return f"{{{address}}} ~ {distribution}"

    @staticmethod
    def _observe(node: ast.Call, context: Context) -> str:
        # NOTE: because of limitations of the `Gen.jl` framework, the
        # `observe` paradigm is not easily mapped. Therefore, rely on the user
        # specifying the values with the associated addressed outside the
        # model manually. This can be automated in the future, e.g. run two
        # translators for `Gen.jl`, one for the model translation, one for the
        # additionally required `observe` implementations.
        arguments = organize_arguments(
            node.args,
            node.keywords,
            argument_defaults=[ast.Constant(0)],
            keyword_argument_defaults=[
                (2, "address", lambda: ast.Constant(Context.unique_address())),
                (
                    3,
                    "distribution",
                    ast.Call(ast.Name("Dirac"), [ast.Constant(True)], []),
                ),
            ],
        )
        argument_strings = [
            context.translator.visit(argument) for argument in arguments
        ]
        _, address, distribution = argument_strings[:3]
        return f"{{{address}}} ~ {distribution}"

    @staticmethod
    def _vector_array(node: ast.Call, context: Context) -> str:
        def map_datatype(datatype: ast.expr) -> str:
            match datatype:
                case ast.Name("int"):
                    return "Int"
                case ast.Name("float"):
                    return "Float64"
                case ast.Name("bool"):
                    return "Bool"
                case _:
                    # Extend as needed.
                    return str(datatype)

        arguments = list(
            organize_arguments(
                node.args,
                node.keywords,
                argument_defaults=[ast.Constant(1)],
                keyword_argument_defaults=[
                    (2, "fill", ast.Constant(0)),
                    "t",
                ],
            )
        )
        size, fill = arguments[:2]
        size = context.translator.visit(size)
        fill = context.translator.visit(fill)
        if len(arguments) <= 2:
            return f"fill({fill}, {size})"
        else:
            datatype = arguments[2]
            datatype = map_datatype(datatype)
            return f"fill!(Array{{{datatype}}}(undef, {size}), {fill})"

    @staticmethod
    def _indexed_address(node: ast.Call, context: Context) -> str:
        arguments = organize_arguments(
            node.args,
            node.keywords,
            argument_defaults=[lambda: ast.Constant(Context.unique_address())],
        )
        argument_strings = [
            context.translator.visit(argument) for argument in arguments
        ]
        subscriptable, *indices = argument_strings
        return (
            f'"$({subscriptable})['
            + ",".join(f"$({index})" for index in indices)
            + ']"'
        )

    @staticmethod
    def _gamma(node: ast.Call, context: Context) -> str:
        if len(node.args) >= 2:
            node.args[1] = ast.BinOp(ast.Constant(1), ast.Div(), node.args[1])
        mapping = get_function_call_mapping(function_name="gamma")
        return mapping(node, context)

    mappings: dict[str, Callable[[ast.Call, Context], str]] = {
        "sample": _sample,
        "observe": _observe,
        "factor": _unsupported,
        "Vector": _vector_array,
        "Array": _vector_array,
        "IndexedAddress": _indexed_address,
        "IID": _unsupported,
        # Distributions.
        "Dirac": _unsupported,
        "Beta": get_function_call_mapping(function_name="beta"),
        "Cauchy": get_function_call_mapping(function_name="cauchy"),
        "Exponential": get_function_call_mapping(function_name="exponential"),
        "Gamma": _gamma,
        "HalfCauchy": _unsupported,
        "HalfNormal": _unsupported,
        "InverseGamma": get_function_call_mapping(function_name="inv_gamma"),
        "Normal": get_function_call_mapping(function_name="normal"),
        "StudentT": _unsupported,
        "Uniform": get_function_call_mapping(function_name="uniform"),
        "Bernoulli": get_function_call_mapping(function_name="bernoulli"),
        "Binomial": get_function_call_mapping(function_name="binom"),
        "DiscreteUniform": get_function_call_mapping(
            function_name="uniform_discrete"
        ),
        "Geometric": get_function_call_mapping(function_name="geometric"),
        "HyperGeometric": _unsupported,
        "Poisson": get_function_call_mapping(function_name="poisson"),
        "Dirichlet": get_function_call_mapping(function_name="dirichlet"),
        "MultivariateNormal": get_function_call_mapping(
            function_name="mvnormal"
        ),
    }
