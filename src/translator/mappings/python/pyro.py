"""This file contains mappings specific for the Pyro framework.

Note that this builds on top of the more general mapping provided by
`./syntax.py`.

Each mapping is implemented as a class inheriting from `BaseMapping`.
Therefore, view the documentation of that class in case of changes or
additions.
"""

import ast
from typing import Callable, ClassVar

from translator.context import Context
from translator.mappings import MappingError
from translator.mappings.python.syntax import CallMapping as BaseCallMapping
from translator.mappings.utils import (
    get_function_call_mapping,
    get_name,
    organize_arguments,
)

FUNCTION_PREFIX = "pyro."
DISTRIBUTION_PREFIX = "dist."
TORCH_PREFIX = "torch."


def preamble(context: Context) -> None:
    context.line("import pyro")
    context.line("import pyro.distributions as dist")


class CallMapping(BaseCallMapping):
    @staticmethod
    def _get_mapping_with_import(
        imqort: str, mapping: Callable[[ast.Call, Context], str]
    ) -> Callable[[ast.Call, Context], str]:
        def _mapping(node: ast.Call, context: Context) -> str:
            with context.in_preamble(discard_if_present=True) as preamble:
                preamble.line(imqort)
            return mapping(node, context)

        return _mapping

    @staticmethod
    def _unsupported(node: ast.Call, _: Context) -> str:
        raise MappingError(
            f"Pyro doesn't provide an equivalent for `{get_name(node)}`."
        )

    @staticmethod
    def _observe(node: ast.Call, context: Context) -> str:
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
        argument_strings.append(f"obs={argument_strings.pop(0)}")
        mapping = get_function_call_mapping(
            function_name=f"{FUNCTION_PREFIX}sample",
            arguments=argument_strings,
        )
        return mapping(node, context)

    @staticmethod
    def _factor(node: ast.Call, context: Context) -> str:
        arguments = list(
            organize_arguments(
                node.args,
                node.keywords,
                argument_defaults=[ast.Constant(0)],
                keyword_argument_defaults=[
                    (
                        2,
                        "address",
                        lambda: ast.Constant(Context.unique_address()),
                    )
                ],
            )
        )
        arguments[0], arguments[1] = arguments[1], arguments[0]
        mapping = get_function_call_mapping(
            function_name=f"{FUNCTION_PREFIX}factor",
            arguments=arguments,
        )
        return mapping(node, context)

    @staticmethod
    def _vector_array(node: ast.Call, context: Context) -> str:
        def map_datatype(datatype: ast.expr) -> str:
            match datatype:
                case ast.Name(id):
                    return id
                case _:
                    return str(datatype)

        with context.in_preamble(discard_if_present=True) as preamble:
            preamble.line("import torch")
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
        if not isinstance(arguments[0], (ast.List, ast.Tuple)):
            arguments[0] = ast.Tuple([arguments[0]])
        datatype = (
            map_datatype(arguments.pop(2)) if len(arguments) >= 3 else None
        )
        argument_strings = [
            context.translator.visit(argument) for argument in arguments
        ]
        if datatype is not None:
            argument_strings.append(f"dtype={datatype}")
        mapping = get_function_call_mapping(
            function_name=f"{TORCH_PREFIX}full", arguments=argument_strings
        )
        return mapping(node, context)

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
            f'f"{{{subscriptable}}}['
            + ",".join(f"{{{index}}}" for index in indices)
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
        if not isinstance(arguments[1], (ast.List, ast.Tuple)):
            arguments[1] = ast.Tuple([arguments[1]])
        argument_strings = [
            context.translator.visit(argument) for argument in arguments
        ]
        distribution, size = argument_strings[:2]
        return f"{distribution}.expand({size})"

    @staticmethod
    def _half_cauchy_half_normal(node: ast.Call, context: Context) -> str:
        name = get_name(node)
        arguments = list(organize_arguments(node.args, node.keywords))
        match arguments:
            case [] | [_]:
                pass
            case [ast.Constant(0), *_]:
                arguments.pop(0)
            case _:
                raise MappingError(
                    f"Pyro's `{name}` requires `loc`"
                    " (the first argument) to be `0`",
                )
        mapping = get_function_call_mapping(
            function_name=DISTRIBUTION_PREFIX + name,
            arguments=arguments,
        )
        return mapping(node, context)

    @staticmethod
    def _dirichlet(node: ast.Call, context: Context) -> str:
        with context.in_preamble(discard_if_present=True) as preamble:
            preamble.line("import torch")
        mapping = get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Dirichlet",
            arguments=lambda arguments, keyword_arguments, context: (
                f"{TORCH_PREFIX}tensor({context.translator.visit(argument)})"
                for argument in organize_arguments(
                    arguments, keyword_arguments
                )
            ),
        )
        return mapping(node, context)

    mappings: ClassVar[dict[str, Callable[[ast.Call, Context], str]]] = {
        "sample": get_function_call_mapping(
            function_name=f"{FUNCTION_PREFIX}sample"
        ),
        "observe": _observe,
        "factor": _factor,
        "Vector": _vector_array,
        "Array": _vector_array,
        "IndexedAddress": _indexed_address,
        "IID": _iid,
        # Distributions.
        "Dirac": _get_mapping_with_import(
            "import torch",
            get_function_call_mapping(
                function_name=f"{DISTRIBUTION_PREFIX}Delta",
                arguments=lambda arguments, keyword_arguments, context: (
                    f"{TORCH_PREFIX}tensor({context.translator.visit(argument)})"
                    for argument in organize_arguments(
                        arguments, keyword_arguments
                    )
                ),
            ),
        ),
        "Beta": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Beta"
        ),
        "Cauchy": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Cauchy"
        ),
        "Exponential": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Exponential"
        ),
        "Gamma": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Gamma"
        ),
        "HalfCauchy": _half_cauchy_half_normal,
        "HalfNormal": _half_cauchy_half_normal,
        "InverseGamma": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}InverseGamma"
        ),
        "Normal": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Normal"
        ),
        "StudentT": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}StudentT"
        ),
        "Uniform": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Uniform"
        ),
        "Bernoulli": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Bernoulli"
        ),
        "Binomial": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Binomial"
        ),
        "DiscreteUniform": _unsupported,
        "Geometric": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Geometric"
        ),
        "HyperGeometric": _unsupported,
        "Poisson": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Poisson"
        ),
        "Dirichlet": _get_mapping_with_import(
            "import torch",
            get_function_call_mapping(
                function_name=f"{DISTRIBUTION_PREFIX}Dirichlet",
                arguments=lambda arguments, keyword_arguments, context: (
                    f"{TORCH_PREFIX}tensor({context.translator.visit(argument)})"
                    for argument in organize_arguments(
                        arguments, keyword_arguments
                    )
                ),
            ),
        ),
        "MultivariateNormal": _get_mapping_with_import(
            "import torch",
            get_function_call_mapping(
                function_name=f"{DISTRIBUTION_PREFIX}MultivariateNormal",
                arguments=lambda arguments, keyword_arguments, context: (
                    f"{TORCH_PREFIX}tensor({context.translator.visit(argument)})"
                    for argument in organize_arguments(
                        arguments, keyword_arguments
                    )
                ),
            ),
        ),
        "Categorical": get_function_call_mapping(
            function_name=f"{DISTRIBUTION_PREFIX}Categorical"
        ),
    }
