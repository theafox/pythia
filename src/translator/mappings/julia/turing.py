"""This file contains mappings specific for the Turing framework.

Note that this builds on top of the more general mapping provided by
`./syntax.py`.

Each mapping is implemented as a class inheriting from `BaseMapping`.
Therefore, view the documentation of that class in case of changes or
additions.
"""

import ast
from typing import Callable, ClassVar, Iterable, override

from translator.context import Context
from translator.mappings import MappingError
from translator.mappings.julia.syntax import (
    AssignmentMapping as BaseAssignmentMapping,
)
from translator.mappings.julia.syntax import CallMapping as BaseCallMapping
from translator.mappings.julia.syntax import (
    FunctionMapping as BaseFunctionMapping,
)
from translator.mappings.utils import (
    get_function_call_mapping,
    get_name,
    organize_arguments,
)


def _compare_target_to_address(target: ast.expr, address: ast.expr) -> None:
    def _extract_identifiers(expression: ast.expr) -> list[str]:
        variables: list[str] = []

        class IdentifierVisitor(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name) -> None:  # noqa
                if node.id == "IndexedAddress":
                    return
                variables.append(node.id)

        IdentifierVisitor().visit(expression)
        return variables

    target_variables = _extract_identifiers(target)
    address_variables = _extract_identifiers(address)

    # The "initial" variable of the target may be counted as a constant since
    # it is not variable in the complexity sense regarding the address.
    if len(target_variables) >= 1:
        target_variables.pop(0)

    target_variables.sort()
    address_variables.sort()
    if target_variables != address_variables:
        raise MappingError(
            "The assignment variable's and address' complexity do not"
            f" coincide: {*target_variables,} versus {*address_variables,}."
        )


def preamble(context: Context) -> None:
    context.line("using Turing")


class FunctionMapping(BaseFunctionMapping):
    macros: Iterable[str] = ["model"]


class AssignmentMapping(BaseAssignmentMapping):
    @override
    @classmethod
    def map(cls, node: ast.AST, context: Context) -> str | None:
        match node:
            case (
                ast.Assign(targets=[target, *_], value=ast.Call() as call)
                | ast.AnnAssign(target=target, value=ast.Call() as call)
            ) if get_name(call) == "sample":
                # NOTE: since Turing doesn't use explicit addresses, discard
                # the address and merely use the assignment target.
                arguments = organize_arguments(
                    call.args,
                    call.keywords,
                    argument_defaults=[
                        lambda: ast.Constant(Context.unique_address()),
                        ast.Call(ast.Name("Dirac"), [ast.Constant(True)], []),
                    ],
                )
                address, distribution = list(arguments)[:2]
                _compare_target_to_address(
                    target, address
                )  # pass on `MappingError`.
                target = context.translator.visit(target)
                distribution = context.translator.visit(distribution)
                context.line(f"{target} ~ {distribution}")
                return None
            case _:
                return super().map(node, context)


class CallMapping(BaseCallMapping):
    @staticmethod
    def _unsupported(node: ast.Call, _: Context) -> str:
        raise MappingError(
            f"Turing doesn't provide an equivalent for `{get_name(node)}`."
        )

    @staticmethod
    def _sample(node: ast.Call, context: Context) -> str:
        # NOTE: In case `sample` was used in an assignment (as intended) the
        # assignment mapping will catch the translation and this will not be
        # called.
        raise MappingError(
            "Due to limitations with Turing, `sample` may only be used as a"
            " value in assignments."
        )

    @staticmethod
    def _observe(node: ast.Call, context: Context) -> str:
        # NOTE: Since Turing doesn't use explicit addresses, discard the
        # address and merely use the assignment target.
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
        value, address, distribution = list(arguments)[:3]
        _compare_target_to_address(value, address)  # pass on `MappingError`.
        value = context.translator.visit(value)
        distribution = context.translator.visit(distribution)
        return f"{value} ~ {distribution}"

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
    def _iid(node: ast.Call, context: Context) -> str:
        arguments = list(
            organize_arguments(
                node.args,
                node.keywords,
                argument_defaults=[
                    ast.Call(ast.Name("Dirac"), [ast.Constant(True)], []),
                    ast.Constant(1),
                ],
            )
        )
        distribution, size = arguments[0], arguments[1]
        if not isinstance(size, (ast.List, ast.Tuple)):
            size = ast.Tuple([size])
        distribution = context.translator.visit(distribution)
        size = ", ".join(context.translator.visit(item) for item in size.elts)
        return f"filldist({distribution}, {size})"

    @staticmethod
    def _exponential(node: ast.Call, context: Context) -> str:
        if len(node.args) >= 1:
            node.args[0] = ast.BinOp(ast.Constant(1), ast.Div(), node.args[1])
        mapping = get_function_call_mapping()
        return mapping(node, context)

    @staticmethod
    def _gamma(node: ast.Call, context: Context) -> str:
        if len(node.args) >= 2:
            node.args[1] = ast.BinOp(ast.Constant(1), ast.Div(), node.args[1])
        mapping = get_function_call_mapping()
        return mapping(node, context)

    @staticmethod
    def _half_cauchy_half_normal(node: ast.Call, context: Context) -> str:
        mapping = get_function_call_mapping()
        node.func = ast.Name(get_name(node).removeprefix("Half"))
        location = (
            context.translator.visit(node.args.pop(0))
            if len(node.args) >= 2
            else "0"
        )
        distribution = mapping(node, context)
        return f"Truncated({distribution}, {location}, +Inf)"

    @staticmethod
    def _dirichlet(node: ast.Call, context: Context) -> str:
        arguments = list(
            organize_arguments(
                node.args,
                node.keywords,
                argument_defaults=[ast.Constant(1)],
                keyword_argument_defaults=[(2, "size", ast.Constant(1))],
            )
        )
        arguments[0], arguments[1] = arguments[1], arguments[0]
        node.args = arguments
        mapping = get_function_call_mapping()
        return mapping(node, context)

    @staticmethod
    def _categorical(node: ast.Call, context: Context) -> str:
        # Special mapping is required since the default `Categorical` provided
        # in Turing returns indices according to Julia's standard, 1-based.
        # Additionally, this needs to be translated using a placeholder. The
        # reason being, the contents of the argument are needed twice and using
        # them as is may introduce bugs in case the expression has
        # side-effects.
        arguments = organize_arguments(
            node.args, node.keywords, argument_defaults=[ast.List]
        )
        argument_strings = [
            context.translator.visit(argument) for argument in arguments
        ]
        if len(argument_strings) >= 1:
            argument_placeholder = "__categorical" + context.unique_address()
            probabilities = argument_strings.pop(0)
            context.line(f"{argument_placeholder} = {probabilities}")
            argument_strings = [
                f"0:length({argument_placeholder})-1",
                argument_placeholder,
                *argument_strings,
            ]
        mapping = get_function_call_mapping(
            function_name="DiscreteNonParametric", arguments=argument_strings
        )
        return mapping(node, context)

    mappings: ClassVar[dict[str, Callable[[ast.Call, Context], str]]] = {
        "sample": _sample,
        "observe": _observe,
        "factor": _unsupported,
        "Vector": _vector_array,
        "Array": _vector_array,
        "IndexedAddress": _indexed_address,
        "IID": _iid,
        # Distributions.
        "Dirac": get_function_call_mapping(),
        "Beta": get_function_call_mapping(),
        "Cauchy": get_function_call_mapping(),
        "Exponential": _exponential,
        "Gamma": _gamma,
        "HalfCauchy": _half_cauchy_half_normal,
        "HalfNormal": _half_cauchy_half_normal,
        "InverseGamma": get_function_call_mapping(),
        "Normal": get_function_call_mapping(),
        "StudentT": get_function_call_mapping(function_name="TDist"),
        "Uniform": get_function_call_mapping(),
        "Bernoulli": get_function_call_mapping(),
        "Binomial": get_function_call_mapping(),
        "DiscreteUniform": get_function_call_mapping(),
        "Geometric": get_function_call_mapping(),
        "HyperGeometric": get_function_call_mapping(
            function_name="Hypergeometric"
        ),
        "Poisson": get_function_call_mapping(),
        "Dirichlet": _dirichlet,
        "MultivariateNormal": get_function_call_mapping(
            function_name="MvNormal"
        ),
        "Categorical": _categorical,
    }
